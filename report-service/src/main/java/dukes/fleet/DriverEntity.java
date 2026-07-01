/********************************************************************************
 * CoreFleet — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.fleet;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import jakarta.json.bind.annotation.JsonbTransient;

/** A driver and their accumulated stats across trips. */
public class DriverEntity {

    private static final int HISTORY_CAP = 100;

    private String did;
    private String name = "";
    private String surname = "";
    private String cf = "";
    private String nationality = "";
    private int trips;
    private double totalKm;
    private int infractions;   // speeding trips (fines)
    private int warnings;      // trips with harsh events
    private final List<TripScore> scoreHistory = new ArrayList<>();

    // report cache (not serialized in registry responses)
    private String lastReportHash;
    private DriverReport lastReport;

    public DriverEntity() {
    }

    public DriverEntity(String did) {
        this.did = did;
    }

    public synchronized void addTrip(TripScore t, boolean infraction, boolean warning) {
        trips++;
        totalKm += t.distKm();
        if (infraction) infractions++;
        if (warning) warnings++;
        scoreHistory.add(t);
        while (scoreHistory.size() > HISTORY_CAP) scoreHistory.remove(0);
    }

    public void setAnagrafica(String name, String surname, String cf, String nationality) {
        if (name != null && !name.isBlank()) this.name = name;
        if (surname != null && !surname.isBlank()) this.surname = surname;
        if (cf != null && !cf.isBlank()) this.cf = cf;
        if (nationality != null && !nationality.isBlank()) this.nationality = nationality;
    }

    public String getDid() {
        return did;
    }

    public String getName() {
        return name;
    }

    public String getSurname() {
        return surname;
    }

    public String getCf() {
        return cf;
    }

    public String getNationality() {
        return nationality;
    }

    public String getFullName() {
        return (name + " " + surname).trim();
    }

    public int getTrips() {
        return trips;
    }

    public double getTotalKm() {
        return Math.round(totalKm * 10.0) / 10.0;
    }

    public int getInfractions() {
        return infractions;
    }

    public int getWarnings() {
        return warnings;
    }

    public double getAvgSafety() {
        return avg(true);
    }

    public double getAvgEco() {
        return avg(false);
    }

    private double avg(boolean safety) {
        if (scoreHistory.isEmpty()) return 0;
        double sum = 0;
        for (TripScore t : scoreHistory) sum += safety ? t.safety() : t.eco();
        return Math.round((sum / scoreHistory.size()) * 10.0) / 10.0;
    }

    /** Behaviours that recur across two or more of this driver's trips. */
    public List<String> getRecidivist() {
        Map<String, Integer> counts = new LinkedHashMap<>();
        for (TripScore t : scoreHistory) {
            if (t.flags() == null) continue;
            for (String f : t.flags()) counts.merge(f, 1, Integer::sum);
        }
        List<String> out = new ArrayList<>();
        counts.forEach((k, v) -> {
            if (v >= 2) out.add(k);
        });
        return out;
    }

    public List<TripScore> getScoreHistory() {
        return scoreHistory;
    }

    @JsonbTransient
    public String getLastReportHash() {
        return lastReportHash;
    }

    public void setLastReportHash(String h) {
        this.lastReportHash = h;
    }

    @JsonbTransient
    public DriverReport getLastReport() {
        return lastReport;
    }

    public void setLastReport(DriverReport r) {
        this.lastReport = r;
    }
}
