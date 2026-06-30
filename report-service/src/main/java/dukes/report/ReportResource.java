/********************************************************************************
 * CoreFleet SDV — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.report;

import java.io.StringReader;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import jakarta.inject.Inject;
import jakarta.json.Json;
import jakarta.json.JsonArray;
import jakarta.json.JsonObject;
import jakarta.json.JsonReader;
import jakarta.json.JsonValue;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

/**
 * Driving-report endpoint. The report is about the DRIVER.
 *
 *   POST /report/api/report   body = the fleet server's session payload
 *                             -> generates and stores a {@link DrivingReport}
 *   GET  /report/api/report   -> recent reports (newest first)
 *
 * Identity, scores and trend come from the platform (deterministic); the LLM
 * supplies only the narrative, so those fields are overwritten after the call.
 */
@Path("/report")
public class ReportResource {

    @Inject
    DrivingReportAiService ai;

    @Inject
    ReportStore store;

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response generate(String body) {
        if (body == null || body.isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "empty request body")).build();
        }
        try {
            DrivingReport report = ai.analyze(body);
            applyAuthoritativeFields(report, body);
            store.add(report);
            return Response.ok(report).build();
        } catch (Exception e) {
            return Response.status(Response.Status.BAD_GATEWAY)
                    .entity(Map.of("error", "LLM call failed: " + e.getMessage())).build();
        }
    }

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public List<DrivingReport> recent() {
        return store.recent();
    }

    /** Overwrite the model's identity/score/trend fields with the platform's. */
    private static void applyAuthoritativeFields(DrivingReport report, String body) {
        try (JsonReader reader = Json.createReader(new StringReader(body))) {
            JsonObject root = reader.readObject();
            report.setVid(root.getString("vid", report.getVid()));
            report.setDid(root.getString("did", "UNKNOWN"));
            report.setDriverName(root.getString("driverName", report.getDid()));
            report.setTripId(root.getString("tripId", null));

            JsonObject scores = root.containsKey("scores") && !root.isNull("scores")
                    ? root.getJsonObject("scores") : null;
            if (scores != null) {
                int safety = (int) Math.round(num(scores, "safety", report.getSafetyScore()));
                int eco = (int) Math.round(num(scores, "eco", report.getEcoScore()));
                report.setSafetyScore(safety);
                report.setEcoScore(eco);
                report.setOverallGrade(grade((safety + eco) / 2.0));
            }

            if (root.containsKey("trend") && !root.isNull("trend")) {
                report.setTrend(parseTrend(root.getJsonObject("trend")));
            }
        } catch (Exception ignored) {
            // keep the model's values if the payload can't be parsed
        }
    }

    private static Trend parseTrend(JsonObject t) {
        Trend tr = new Trend();
        tr.setVerdict(t.getString("verdict", "stable"));
        tr.setTripCount(t.getInt("tripCount", 1));
        tr.setDeltaSafety(numOrNull(t, "deltaSafety"));
        tr.setDeltaEco(numOrNull(t, "deltaEco"));
        tr.setPrevSafety(numOrNull(t, "prevSafety"));
        tr.setPrevEco(numOrNull(t, "prevEco"));
        tr.setRecidivist(strList(t, "recidivist"));
        return tr;
    }

    private static String grade(double avg) {
        if (avg >= 85) return "A";
        if (avg >= 70) return "B";
        if (avg >= 55) return "C";
        return "D";
    }

    private static double num(JsonObject o, String k, double fallback) {
        return o.containsKey(k) && !o.isNull(k) ? o.getJsonNumber(k).doubleValue() : fallback;
    }

    private static Double numOrNull(JsonObject o, String k) {
        return o.containsKey(k) && !o.isNull(k) ? o.getJsonNumber(k).doubleValue() : null;
    }

    private static List<String> strList(JsonObject o, String k) {
        List<String> out = new ArrayList<>();
        if (o.containsKey(k) && !o.isNull(k)) {
            JsonArray arr = o.getJsonArray(k);
            for (JsonValue v : arr) {
                if (v.getValueType() == JsonValue.ValueType.STRING) {
                    out.add(((jakarta.json.JsonString) v).getString());
                }
            }
        }
        return out;
    }
}
