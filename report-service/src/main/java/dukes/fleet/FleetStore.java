/********************************************************************************
 * CoreFleet, based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.fleet;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import dukes.ai.ImageGenerator;
import dukes.hourglass.HourglassOutput;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.json.Json;
import jakarta.json.JsonArray;
import jakarta.json.JsonObject;
import jakarta.json.JsonObjectBuilder;
import jakarta.json.JsonString;
import jakarta.json.JsonValue;
import org.eclipse.microprofile.config.inject.ConfigProperty;

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

    @Inject
    ImageGenerator imageGenerator;

    @Inject
    @ConfigProperty(name = "report.fine-safety-penalty", defaultValue = "25")
    int finePenalty;

    private final ConcurrentMap<String, DriverEntity> drivers = new ConcurrentHashMap<>();
    private final ConcurrentMap<String, VehicleEntity> vehicles = new ConcurrentHashMap<>();
    // who is driving now, with telemetry, as pushed by the server
    private volatile JsonArray active = JsonValue.EMPTY_JSON_ARRAY;

    // hourglass images, generated separately from the text report
    private final ExecutorService imageExecutor = Executors.newFixedThreadPool(2);
    private final ConcurrentMap<String, String> driverImage = new ConcurrentHashMap<>(); // did -> data URI
    private final Set<String> imageInFlight = ConcurrentHashMap.newKeySet();

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

        // 1) compute the final numbers first
        DriverReport r = new DriverReport();
        applyAuthoritative(r, d);

        // 2) the LLM writes the text from those numbers
        DriverReport narrative = ai.analyze(driverInputJson(d, r));
        r.setSummary(narrative.getSummary());
        r.setStrengths(narrative.getStrengths());
        r.setRecommendations(narrative.getRecommendations());
        r.setMaintenanceHints(narrative.getMaintenanceHints());
        if (narrative.getHourglass() != null) {
            r.setHourglass(narrative.getHourglass());
        }

        // 3) the hourglass image is generated in the background, so the text
        //    report returns right away instead of timing out with a 502
        String existingImg = driverImage.get(did);
        if (existingImg != null) {
            r.setHourglassImageUrl(existingImg);
            r.setImageStatus("ready");
        } else if (imageGenerator.isEnabled()) {
            r.setImageStatus("pending");
            submitImageJob(did, d, r);
        } else {
            r.setImageStatus("none");
        }

        r.setGeneratedAt(System.currentTimeMillis());
        r.setCached(false);

        d.setLastReportHash(hash);
        d.setLastReport(r);
        history.add(r);
        return r;
    }

    private void submitImageJob(String did, DriverEntity d, DriverReport r) {
        if (!imageInFlight.add(did)) return; // already generating for this driver
        imageExecutor.submit(() -> {
            try {
                String url = generateHourglassImage(d, r);
                if (url != null) {
                    driverImage.put(did, url);
                    r.setHourglassImageUrl(url);
                    r.setImageStatus("ready");
                } else {
                    r.setImageStatus("none");
                }
            } catch (Exception e) {
                r.setImageStatus("none");
            } finally {
                imageInFlight.remove(did);
            }
        });
    }

    /** Image status for a driver: "ready" (+url), "pending", or "none". */
    public String driverImageUrl(String did) {
        return driverImage.get(did);
    }

    public boolean driverImagePending(String did) {
        return imageInFlight.contains(did);
    }

    private static String dataHash(DriverEntity d) {
        return d.getTrips() + "|" + (long) d.getTotalKm() + "|" + d.getInfractions()
                + "|" + (long) (d.getAvgSafety() * 10) + "|" + (long) (d.getAvgEco() * 10);
    }

    private void applyAuthoritative(DriverReport r, DriverEntity d) {
        r.setDid(d.getDid());
        r.setDriverName(d.getFullName());
        r.setTripCount(d.getTrips());
        r.setTotalKm(d.getTotalKm());
        r.setInfractions(d.getInfractions());

        // a fine (multa) is a serious policy violation: heavily downgrade safety
        int rawSafety = (int) Math.round(d.getAvgSafety());
        int adjSafety = d.getInfractions() > 0
                ? Math.max(0, rawSafety - finePenalty * d.getInfractions())
                : rawSafety;
        int eco = (int) Math.round(d.getAvgEco());
        r.setAvgSafety(adjSafety);
        r.setAvgEco(eco);
        r.setRecidivist(d.getRecidivist());
        double avg = (adjSafety + eco) / 2.0;
        r.setOverallGrade(avg >= 85 ? "A" : avg >= 70 ? "B" : avg >= 55 ? "C" : "D");
        if (r.getHourglass() == null) {
            r.setHourglass(new HourglassOutput());
        }
    }

    /** Hourglass Model visual (best-effort, may return null). */
    private String generateHourglassImage(DriverEntity d, DriverReport r) {
        HourglassOutput h = r.getHourglass();
        String prompt = "A clean technical infographic drawn as an actual HOURGLASS shape, "
                + "dark navy background with neon blue and purple accents, three labelled tiers: "
                + "wide TOP = Stakeholders (" + join(h == null ? null : h.getStakeholders(),
                        "driver, fleet operations, insurer, city") + "); "
                + "narrow MIDDLE waist = Capabilities / KPIs (" + join(h == null ? null : h.getCapabilities(),
                        "safety score, eco score") + "); "
                + "wide BOTTOM = Standards & Signals (" + join(h == null ? null : h.getStandardsGroups(),
                        "OBD2 PIDs, GPS, IMU") + "). "
                + "Minimal flat vector style, connected-car fleet telemetry theme, high contrast.";
        return imageGenerator.generate(prompt);
    }

    private static String join(List<String> list, String fallback) {
        if (list == null || list.isEmpty()) return fallback;
        return String.join(", ", list.subList(0, Math.min(4, list.size())));
    }

    /** Input for the LLM: the numbers already on the report, so the text quotes
     *  what the dashboard shows, plus the per-trip history for context. */
    private static String driverInputJson(DriverEntity d, DriverReport r) {
        JsonObjectBuilder b = Json.createObjectBuilder()
                .add("did", r.getDid())
                .add("name", r.getDriverName())
                .add("nationality", d.getNationality())
                .add("tripCount", r.getTripCount())
                .add("totalKm", r.getTotalKm())
                .add("infractions", r.getInfractions())
                .add("warnings", d.getWarnings())
                .add("safetyScore", r.getAvgSafety())
                .add("ecoScore", r.getAvgEco())
                .add("overallGrade", r.getOverallGrade());
        var recid = Json.createArrayBuilder();
        (r.getRecidivist() == null ? java.util.List.<String>of() : r.getRecidivist()).forEach(recid::add);
        b.add("recidivist", recid);
        var trips = Json.createArrayBuilder();
        for (TripScore t : d.getScoreHistory()) {
            trips.add(Json.createObjectBuilder()
                    .add("safety", t.safety()).add("eco", t.eco())
                    .add("distKm", t.distKm()));
        }
        b.add("perTripTrajectory", trips);
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
