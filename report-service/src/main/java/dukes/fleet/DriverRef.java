/********************************************************************************
 * CoreFleet SDV — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.fleet;

/** A driver's recent use of a vehicle (shown on the vehicle detail). */
public record DriverRef(String did, String name, String tripId, double endedAt) {
}
