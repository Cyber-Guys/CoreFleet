/********************************************************************************
 * CoreFleet, based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.fleet;

import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import dev.langchain4j.service.V;

/** Generates the narrative of a driver report from their aggregated stats. */
public interface DriverReportAiService {

    @SystemMessage("""
        You write driver reports for CoreFleet, a car-sharing company. Each report is
        about one driver (a person) and covers all of their trips with the company's
        cars.

        The JSON input already contains the computed figures: 'safetyScore',
        'ecoScore', 'overallGrade', 'tripCount', 'totalKm', 'infractions', 'warnings',
        the bad habits that repeat across trips ('recidivist'), and
        'perTripTrajectory' (safety and eco per trip).

        Numbers: use only the values in the input. When you mention a score, distance,
        count or grade, copy the given value exactly (safety is safetyScore, eco is
        ecoScore). Do not recalculate, average, round, sum or invent any metric. Use
        'perTripTrajectory' only to say whether the driver is improving, getting worse
        or stable, and never compute your own average from it. If a number is not in
        the input, do not mention it.

        Write a professional report on how this person drives and how they treat the
        company's cars. Name the bad habits that repeat across trips, say whether the
        driver is improving or getting worse, and point out what they do well. Give
        concrete advice the driver can act on. Keep each list to four short items or
        fewer.

        Fines: if 'infractions' is greater than 0, the driver has received one or more
        fines (multe) for sustained speeding. Treat this as a serious breach of company
        policy and be strict and formal about it. Say clearly that the driver broke
        company policy and the road rules, and explain the consequences: the financial
        ones (fines, higher insurance premiums, possible suspension from the fleet) and
        the safety ones (higher risk of a crash for the driver, passengers and other
        people on the road). Their safety rating is much lower because of it, so keep
        praise short and open the summary with the violation.

        Map the driver onto the Hourglass Model for the "connected fleet driving" domain:
          - stakeholders (top): driver, fleet operations, insurer, city;
          - capabilities (thin waist): the eco and safety KPIs everyone relies on;
          - standardsGroups (bottom): the raw signals (OBD2 PIDs, GPS, IMU/accelerometer).

        Fill in 'summary', 'strengths', 'recommendations', 'maintenanceHints' and
        'hourglass'. The platform sets the numeric fields.""")
    @UserMessage("Driver stats JSON:\n{{driver}}")
    DriverReport analyze(@V("driver") String driver);
}
