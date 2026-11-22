/********************************************************************************
 * CoreFleet, based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.fleet;

import java.util.List;

/** One trip's outcome in a driver's history. */
public record TripScore(
        String tripId,
        String vid,
        double safety,
        double eco,
        double distKm,
        List<String> flags,
        double endedAt) {
}
