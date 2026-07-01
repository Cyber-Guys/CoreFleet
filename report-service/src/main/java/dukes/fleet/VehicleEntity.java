/********************************************************************************
 * CoreFleet — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.fleet;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

/** A car and its current asset state. */
public class VehicleEntity {

    private static final int RECENT_DRIVERS = 6;

    private String vid;
    private double odoKm;
    private int tripCount;
    private double fuelPct = 100;
    private double oilPct = 100;
    private List<String> lights = new ArrayList<>();
    private final Deque<DriverRef> recentDrivers = new ArrayDeque<>();
    private double lastUpdated;

    public VehicleEntity() {
    }

    public VehicleEntity(String vid) {
        this.vid = vid;
    }

    public synchronized void update(double odoKm, double fuelPct, double oilPct,
                                    List<String> lights, DriverRef driver, double when) {
        this.odoKm = odoKm;
        this.fuelPct = fuelPct;
        this.oilPct = oilPct;
        this.lights = lights != null ? lights : new ArrayList<>();
        this.tripCount++;
        this.lastUpdated = when;
        recentDrivers.addFirst(driver);
        while (recentDrivers.size() > RECENT_DRIVERS) recentDrivers.removeLast();
    }

    public String getVid() {
        return vid;
    }

    public double getOdoKm() {
        return Math.round(odoKm * 10.0) / 10.0;
    }

    public int getTripCount() {
        return tripCount;
    }

    public double getFuelPct() {
        return fuelPct;
    }

    public double getOilPct() {
        return oilPct;
    }

    public List<String> getLights() {
        return lights;
    }

    public List<DriverRef> getRecentDrivers() {
        return new ArrayList<>(recentDrivers);
    }

    public double getLastUpdated() {
        return lastUpdated;
    }
}
