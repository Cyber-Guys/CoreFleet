/********************************************************************************
 * CoreFleet, based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.fleet;

import java.util.List;
import java.util.Map;

import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

@Path("/vehicles")
@Produces(MediaType.APPLICATION_JSON)
public class VehiclesResource {

    @Inject
    FleetStore store;

    @GET
    public List<VehicleEntity> list() {
        return store.listVehicles();
    }

    @GET
    @Path("{vid}")
    public Response one(@PathParam("vid") String vid) {
        VehicleEntity v = store.getVehicle(vid);
        if (v == null) {
            return Response.status(Response.Status.NOT_FOUND)
                    .entity(Map.of("error", "vehicle not found")).build();
        }
        return Response.ok(v).build();
    }
}
