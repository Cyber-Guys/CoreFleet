/********************************************************************************
 * CoreFleet, based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.fleet;

import java.util.List;

import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;

/** History of generated driver reports (newest first). */
@Path("/report")
@Produces(MediaType.APPLICATION_JSON)
public class ReportsHistoryResource {

    @Inject
    ReportHistory history;

    @GET
    public List<DriverReport> recent() {
        return history.recent();
    }
}
