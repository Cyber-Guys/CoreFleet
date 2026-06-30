/********************************************************************************
 * CoreFleet SDV — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.report;

import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.concurrent.ConcurrentLinkedDeque;

import jakarta.enterprise.context.ApplicationScoped;

/** Bounded in-memory history of generated reports (newest first). */
@ApplicationScoped
public class ReportStore {

    private static final int MAX = 50;
    private final Deque<DrivingReport> reports = new ConcurrentLinkedDeque<>();

    public void add(DrivingReport report) {
        reports.addFirst(report);
        while (reports.size() > MAX) {
            reports.pollLast();
        }
    }

    public List<DrivingReport> recent() {
        return new ArrayList<>(reports);
    }
}
