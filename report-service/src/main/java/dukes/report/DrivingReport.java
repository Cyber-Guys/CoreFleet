/********************************************************************************
 * CoreFleet SDV — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.report;

import java.util.List;

import dukes.hourglass.HourglassOutput;

/**
 * LLM-generated driving report for a single session. Numeric scores stay
 * grounded in the telemetry; the narrative and the hourglass mapping are the
 * model's contribution.
 */
public class DrivingReport {
    private String did;            // driver id (the person scored)
    private String driverName;
    private String vid;            // car driven this trip
    private String tripId;
    private String overallGrade;   // A | B | C | D
    private int safetyScore;       // 0-100
    private int ecoScore;          // 0-100
    private String summary;        // short narrative grounded in the numbers
    private List<String> strengths;
    private List<String> recommendations;
    private List<String> maintenanceHints;
    private Trend trend;           // behaviour vs the driver's previous trips
    private HourglassOutput hourglass; // domain mapping for "connected fleet driving"

    public String getDid() {
        return did;
    }

    public void setDid(String did) {
        this.did = did;
    }

    public String getDriverName() {
        return driverName;
    }

    public void setDriverName(String driverName) {
        this.driverName = driverName;
    }

    public String getVid() {
        return vid;
    }

    public void setVid(String vid) {
        this.vid = vid;
    }

    public String getTripId() {
        return tripId;
    }

    public void setTripId(String tripId) {
        this.tripId = tripId;
    }

    public Trend getTrend() {
        return trend;
    }

    public void setTrend(Trend trend) {
        this.trend = trend;
    }

    public String getOverallGrade() {
        return overallGrade;
    }

    public void setOverallGrade(String overallGrade) {
        this.overallGrade = overallGrade;
    }

    public int getSafetyScore() {
        return safetyScore;
    }

    public void setSafetyScore(int safetyScore) {
        this.safetyScore = safetyScore;
    }

    public int getEcoScore() {
        return ecoScore;
    }

    public void setEcoScore(int ecoScore) {
        this.ecoScore = ecoScore;
    }

    public String getSummary() {
        return summary;
    }

    public void setSummary(String summary) {
        this.summary = summary;
    }

    public List<String> getStrengths() {
        return strengths;
    }

    public void setStrengths(List<String> strengths) {
        this.strengths = strengths;
    }

    public List<String> getRecommendations() {
        return recommendations;
    }

    public void setRecommendations(List<String> recommendations) {
        this.recommendations = recommendations;
    }

    public List<String> getMaintenanceHints() {
        return maintenanceHints;
    }

    public void setMaintenanceHints(List<String> maintenanceHints) {
        this.maintenanceHints = maintenanceHints;
    }

    public HourglassOutput getHourglass() {
        return hourglass;
    }

    public void setHourglass(HourglassOutput hourglass) {
        this.hourglass = hourglass;
    }
}
