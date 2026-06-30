/********************************************************************************
 * CoreFleet SDV — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.report;

import java.util.List;

/** A driver's behaviour this trip relative to their previous trips. */
public class Trend {
    private String verdict;        // first_trip | improved | worsened | stable
    private int tripCount;
    private Double deltaSafety;    // vs the driver's previous average (null on first trip)
    private Double deltaEco;
    private Double prevSafety;
    private Double prevEco;
    private List<String> recidivist; // bad behaviours recurring across trips

    public String getVerdict() {
        return verdict;
    }

    public void setVerdict(String verdict) {
        this.verdict = verdict;
    }

    public int getTripCount() {
        return tripCount;
    }

    public void setTripCount(int tripCount) {
        this.tripCount = tripCount;
    }

    public Double getDeltaSafety() {
        return deltaSafety;
    }

    public void setDeltaSafety(Double deltaSafety) {
        this.deltaSafety = deltaSafety;
    }

    public Double getDeltaEco() {
        return deltaEco;
    }

    public void setDeltaEco(Double deltaEco) {
        this.deltaEco = deltaEco;
    }

    public Double getPrevSafety() {
        return prevSafety;
    }

    public void setPrevSafety(Double prevSafety) {
        this.prevSafety = prevSafety;
    }

    public Double getPrevEco() {
        return prevEco;
    }

    public void setPrevEco(Double prevEco) {
        this.prevEco = prevEco;
    }

    public List<String> getRecidivist() {
        return recidivist;
    }

    public void setRecidivist(List<String> recidivist) {
        this.recidivist = recidivist;
    }
}
