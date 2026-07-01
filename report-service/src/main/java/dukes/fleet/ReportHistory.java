/********************************************************************************
 * CoreFleet — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.fleet;

import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.concurrent.ConcurrentLinkedDeque;

import jakarta.enterprise.context.ApplicationScoped;

/** Bounded history of generated driver reports (newest first). */
@ApplicationScoped
public class ReportHistory {

    private static final int MAX = 100;
    private final Deque<DriverReport> reports = new ConcurrentLinkedDeque<>();

    public void add(DriverReport report) {
        reports.addFirst(report);
        while (reports.size() > MAX) reports.pollLast();
    }

    public List<DriverReport> recent() {
        return new ArrayList<>(reports);
    }
}
