/********************************************************************************
 * CoreFleet SDV — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.fleet;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

import dukes.hourglass.HourglassOutput;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.json.Json;
import jakarta.json.JsonArray;
import jakarta.json.JsonObject;
import jakarta.json.JsonObjectBuilder;
import jakarta.json.JsonString;
import jakarta.json.JsonValue;

/**
 * In-memory fleet registry: accumulates driver and vehicle stats from ingested
 * trips, and generates (or returns cached) per-driver LLM reports.
 */
@ApplicationScoped
public class FleetStore {

    @Inject
    DriverReportAiService ai;

    @Inject
    ReportHistory history;

    private final ConcurrentMap<String, DriverEntity> drivers = new ConcurrentHashMap<>();
    private final ConcurrentMap<String, VehicleEntity> vehicles = new ConcurrentHashMap<>();
    // live "who is driving now" + telemetry, pushed by the server (passthrough)
    private volatile JsonArray active = JsonValue.EMPTY_JSON_ARRAY;

    // --- ingest -------------------------------------------------------------
    public void ingest(JsonObject trip) {
        JsonObject driver = obj(trip, "driver");
        JsonObject vehicle = obj(trip, "vehicle");
        JsonObject session = obj(trip, "session");
        JsonObject scores = obj(trip, "scores");
        List<String> flags = strList(trip, "flags");

        String tripId = str(trip, "tripId", "");
        double endedAt = num(trip, "endedAt", 0);

        String did = str(driver, "did", "UNKNOWN");
        String name = str(driver, "name", did);
        DriverEntity d = drivers.computeIfAbsent(did, DriverEntity::new);
        d.setAnagrafica(name, str(driver, "surname", ""), str(driver, "cf", ""),
                str(driver, "nationality", ""));

        double dist = num(session, "dist_km", 0);
        double safety = num(scores, "safety", 0);
        double eco = num(scores, "eco", 0);
        boolean infraction = flags.contains("speeding");
        boolean warning = flags.contains("harsh_accel") || flags.contains("harsh_brake");
        String vid = str(vehicle, "vid", str(session, "vid", "?"));
        d.addTrip(new TripScore(tripId, vid, safety, eco, dist, flags, endedAt), infraction, warning);

        VehicleEntity v = vehicles.computeIfAbsent(vid, VehicleEntity::new);
        v.update(num(vehicle, "odo_km", 0), num(vehicle, "fuel_pct", 100),
                num(vehicle, "oil_pct", 100), strList(vehicle, "lights"),
                new DriverRef(did, name, tripId, endedAt), endedAt);
    }

    // --- queries ------------------------------------------------------------
    public List<DriverEntity> listDrivers() {
        return new ArrayList<>(drivers.values());
    }

    public DriverEntity getDriver(String did) {
        return drivers.get(did);
    }

    public List<VehicleEntity> listVehicles() {
        return new ArrayList<>(vehicles.values());
    }

    public VehicleEntity getVehicle(String vid) {
        return vehicles.get(vid);
    }

    // --- live "who is driving now" (+ telemetry) ----------------------------
    public void setActive(JsonArray a) {
        this.active = a != null ? a : JsonValue.EMPTY_JSON_ARRAY;
    }

    public JsonArray listActive() {
        return active;
    }

    // --- report generation (with cache) ------------------------------------
    public synchronized DriverReport reportForDriver(String did) {
        DriverEntity d = drivers.get(did);
        if (d == null) return null;

        String hash = dataHash(d);
        if (hash.equals(d.getLastReportHash()) && d.getLastReport() != null) {
            DriverReport cached = d.getLastReport();
            cached.setCached(true);
            return cached;
        }

        DriverReport r = ai.analyze(driverInputJson(d));
        applyAuthoritative(r, d);
        r.setGeneratedAt(System.currentTimeMillis());
        r.setCached(false);

        d.setLastReportHash(hash);
        d.setLastReport(r);
        history.add(r);
        return r;
    }

    private static String dataHash(DriverEntity d) {
        return d.getTrips() + "|" + (long) d.getTotalKm() + "|" + d.getInfractions()
                + "|" + (long) (d.getAvgSafety() * 10) + "|" + (long) (d.getAvgEco() * 10);
    }

    private static void applyAuthoritative(DriverReport r, DriverEntity d) {
        r.setDid(d.getDid());
        r.setDriverName(d.getFullName());
        r.setTripCount(d.getTrips());
        r.setTotalKm(d.getTotalKm());
        r.setInfractions(d.getInfractions());
        r.setAvgSafety((int) Math.round(d.getAvgSafety()));
        r.setAvgEco((int) Math.round(d.getAvgEco()));
        r.setRecidivist(d.getRecidivist());
        double avg = (d.getAvgSafety() + d.getAvgEco()) / 2.0;
        r.setOverallGrade(avg >= 85 ? "A" : avg >= 70 ? "B" : avg >= 55 ? "C" : "D");
        if (r.getHourglass() == null) {
            r.setHourglass(new HourglassOutput());
        }
    }

    private static String driverInputJson(DriverEntity d) {
        JsonObjectBuilder b = Json.createObjectBuilder()
                .add("did", d.getDid())
                .add("name", d.getFullName())
                .add("nationality", d.getNationality())
                .add("trips", d.getTrips())
                .add("totalKm", d.getTotalKm())
                .add("infractions", d.getInfractions())
                .add("warnings", d.getWarnings())
                .add("avgSafety", d.getAvgSafety())
                .add("avgEco", d.getAvgEco());
        var recid = Json.createArrayBuilder();
        d.getRecidivist().forEach(recid::add);
        b.add("recidivist", recid);
        var trips = Json.createArrayBuilder();
        for (TripScore t : d.getScoreHistory()) {
            trips.add(Json.createObjectBuilder()
                    .add("safety", t.safety()).add("eco", t.eco())
                    .add("distKm", t.distKm()));
        }
        b.add("perTrip", trips);
        return b.build().toString();
    }

    // --- json helpers -------------------------------------------------------
    private static JsonObject obj(JsonObject o, String k) {
        return o != null && o.containsKey(k) && !o.isNull(k)
                ? o.getJsonObject(k) : JsonValue.EMPTY_JSON_OBJECT;
    }

    private static String str(JsonObject o, String k, String def) {
        return o != null && o.containsKey(k) && !o.isNull(k) ? o.getString(k, def) : def;
    }

    private static double num(JsonObject o, String k, double def) {
        return o != null && o.containsKey(k) && !o.isNull(k) ? o.getJsonNumber(k).doubleValue() : def;
    }

    private static List<String> strList(JsonObject o, String k) {
        List<String> out = new ArrayList<>();
        if (o != null && o.containsKey(k) && !o.isNull(k)) {
            JsonArray arr = o.getJsonArray(k);
            for (JsonValue v : arr) {
                if (v.getValueType() == JsonValue.ValueType.STRING) {
                    out.add(((JsonString) v).getString());
                }
            }
        }
        return out;
    }
}
