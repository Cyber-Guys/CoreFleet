/********************************************************************************
 * CoreFleet SDV — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.report;

import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import dev.langchain4j.service.V;

/**
 * Turns a session telemetry summary (the JSON the fleet server emits on
 * shutdown) into a structured {@link DrivingReport}.
 */
public interface DrivingReportAiService {

    @SystemMessage("""
        You are a fleet-analytics assistant for CoreFleet, a car-sharing company.
        A report is about the DRIVER (the person), not the car. The same driver does
        several trips with different cars over time.

        You receive one trip as JSON: 'driverName'/'did' (the driver), 'vid' (the car
        used), and a 'session' aggregate (distance, duration, speeds, rpm, fuel,
        l/100km, and event counters: harsh acceleration/braking, over-rev,
        cold-engine over-rev, idle, speeding seconds). A 'trend' object compares this
        trip to the driver's previous trips: 'verdict' (first_trip/improved/worsened/
        stable), score deltas, and 'recidivist' (bad behaviours that recur trip after
        trip).

        Write a concise, professional report ABOUT THE DRIVER. Ground every statement
        in the numbers; never invent values. Use the trend: praise improvement, flag
        recurring (recidivist) bad habits explicitly as a pattern across trips, and
        note when nothing changed. Give concrete, actionable advice. Keep each list to
        at most four short items.

        Map the trip onto the Hourglass Model for the "connected fleet driving" domain:
          - stakeholders (top): driver, fleet operations, insurer, city;
          - capabilities (thin waist): the normalized eco/safety KPIs everyone relies on;
          - standardsGroups (bottom): the raw signals (OBD2 PIDs, GPS, IMU/accelerometer).

        Write 'summary', 'strengths', 'recommendations', 'maintenanceHints' and
        'hourglass'. The numeric scores and trend are authoritative and set by the
        platform; focus on the narrative.""")
    @UserMessage("Trip report JSON:\n{{session}}")
    DrivingReport analyze(@V("session") String session);
}
