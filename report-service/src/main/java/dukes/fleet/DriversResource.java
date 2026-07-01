/********************************************************************************
 * CoreFleet SDV — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.fleet;

import java.util.List;
import java.util.Map;

import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

@Path("/drivers")
@Produces(MediaType.APPLICATION_JSON)
public class DriversResource {

    @Inject
    FleetStore store;

    @GET
    public List<DriverEntity> list() {
        return store.listDrivers();
    }

    @GET
    @Path("{did}")
    public Response one(@PathParam("did") String did) {
        DriverEntity d = store.getDriver(did);
        if (d == null) {
            return Response.status(Response.Status.NOT_FOUND)
                    .entity(Map.of("error", "driver not found")).build();
        }
        return Response.ok(d).build();
    }

    /** Generate a report for the driver, or return the cached one if their data
     *  hasn't changed since it was last generated. */
    @POST
    @Path("{did}/report")
    public Response report(@PathParam("did") String did) {
        if (store.getDriver(did) == null) {
            return Response.status(Response.Status.NOT_FOUND)
                    .entity(Map.of("error", "driver not found")).build();
        }
        try {
            return Response.ok(store.reportForDriver(did)).build();
        } catch (Exception e) {
            return Response.status(Response.Status.BAD_GATEWAY)
                    .entity(Map.of("error", "LLM call failed: " + e.getMessage())).build();
        }
    }
}
