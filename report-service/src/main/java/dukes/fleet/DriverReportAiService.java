/********************************************************************************
 * CoreFleet SDV — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.fleet;

import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import dev.langchain4j.service.V;

/** Generates the narrative of a driver report from their aggregated stats. */
public interface DriverReportAiService {

    @SystemMessage("""
        You are a fleet-analytics assistant for CoreFleet, a car-sharing company.
        A report is about a DRIVER (a person) and aggregates ALL of their trips with
        the company's cars.

        You receive JSON with the driver's anagrafica, totals (trips, km, infractions),
        average safety/eco scores, the behaviours that recur across trips
        ('recidivist'), and a per-trip list of safety/eco so you can see the trajectory
        over time.

        Write a professional report on how this person drives and treats the company's
        vehicles. Ground every statement in the numbers; never invent values. Explicitly
        call out recidivist (recurring) bad habits as a pattern, note whether the driver
        is improving or worsening over their trips, and praise what is good. Give
        concrete, actionable advice. Keep each list to at most four short items.

        POLICY — FINES: if 'infractions' > 0 the driver has received one or more fines
        (multe) for sustained speeding. Treat this as a SERIOUS policy violation. Be
        strict and formal, do not soften it: state clearly that the driver breached
        company policy and road rules, and spell out the impact — financial (fines,
        higher insurance premiums, possible suspension from the fleet) and safety
        (elevated crash risk for themselves, passengers and the public). Their safety
        standing is heavily downgraded; cut praise accordingly and lead the summary with
        the violation.

        Map the driver onto the Hourglass Model for the "connected fleet driving" domain:
          - stakeholders (top): driver, fleet operations, insurer, city;
          - capabilities (thin waist): the normalized eco/safety KPIs everyone relies on;
          - standardsGroups (bottom): the raw signals (OBD2 PIDs, GPS, IMU/accelerometer).

        Write 'summary', 'strengths', 'recommendations', 'maintenanceHints' and
        'hourglass'. The numeric fields are authoritative and set by the platform.""")
    @UserMessage("Driver stats JSON:\n{{driver}}")
    DriverReport analyze(@V("driver") String driver);
}
