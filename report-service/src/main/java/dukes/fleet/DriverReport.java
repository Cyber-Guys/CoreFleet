/********************************************************************************
 * CoreFleet SDV — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.fleet;

import java.util.List;

import dukes.hourglass.HourglassOutput;

/**
 * LLM-generated report about a DRIVER, aggregating all of their trips. The
 * numeric/identity fields are authoritative (set by the platform); the LLM
 * supplies the narrative and the hourglass mapping.
 */
public class DriverReport {
    private String did;
    private String driverName;
    private int tripCount;
    private double totalKm;
    private int infractions;
    private int avgSafety;
    private int avgEco;
    private String overallGrade;
    private String summary;
    private List<String> strengths;
    private List<String> recommendations;
    private List<String> maintenanceHints;
    private List<String> recidivist;
    private HourglassOutput hourglass;
    private String hourglassImageUrl;   // DALL-E visual of the hourglass model
    private long generatedAt;
    private boolean cached;

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

    public int getTripCount() {
        return tripCount;
    }

    public void setTripCount(int tripCount) {
        this.tripCount = tripCount;
    }

    public double getTotalKm() {
        return totalKm;
    }

    public void setTotalKm(double totalKm) {
        this.totalKm = totalKm;
    }

    public int getInfractions() {
        return infractions;
    }

    public void setInfractions(int infractions) {
        this.infractions = infractions;
    }

    public int getAvgSafety() {
        return avgSafety;
    }

    public void setAvgSafety(int avgSafety) {
        this.avgSafety = avgSafety;
    }

    public int getAvgEco() {
        return avgEco;
    }

    public void setAvgEco(int avgEco) {
        this.avgEco = avgEco;
    }

    public String getOverallGrade() {
        return overallGrade;
    }

    public void setOverallGrade(String overallGrade) {
        this.overallGrade = overallGrade;
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

    public List<String> getRecidivist() {
        return recidivist;
    }

    public void setRecidivist(List<String> recidivist) {
        this.recidivist = recidivist;
    }

    public HourglassOutput getHourglass() {
        return hourglass;
    }

    public void setHourglass(HourglassOutput hourglass) {
        this.hourglass = hourglass;
    }

    public String getHourglassImageUrl() {
        return hourglassImageUrl;
    }

    public void setHourglassImageUrl(String hourglassImageUrl) {
        this.hourglassImageUrl = hourglassImageUrl;
    }

    public long getGeneratedAt() {
        return generatedAt;
    }

    public void setGeneratedAt(long generatedAt) {
        this.generatedAt = generatedAt;
    }

    public boolean isCached() {
        return cached;
    }

    public void setCached(boolean cached) {
        this.cached = cached;
    }
}
