/********************************************************************************
 * CoreFleet — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.fleet;

import java.util.Map;

import jakarta.inject.Inject;
import jakarta.json.JsonArray;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

/**
 * Live "who is driving now" + per-vehicle telemetry. The fleet server pushes it
 * every couple of seconds from the telemetry stream; the dashboard reads it for
 * the connected-vehicles list and the live-trip panel. Stored/served verbatim.
 */
@Path("/active")
public class ActiveResource {

    @Inject
    FleetStore store;

    @POST
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response set(JsonArray body) {
        store.setActive(body);
        return Response.accepted(Map.of("ok", true, "count", body == null ? 0 : body.size())).build();
    }

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public JsonArray list() {
        return store.listActive();
    }
}
