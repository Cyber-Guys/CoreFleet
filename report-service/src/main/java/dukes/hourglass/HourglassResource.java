/********************************************************************************
 * Copyright (c) 2026 Contributors to the Eclipse Foundation
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License v. 2.0 which is available at
 * https://www.eclipse.org/legal/epl-2.0.
 *
 * * SPDX-License-Identifier: EPL-2.0
 ********************************************************************************/
package dukes.hourglass;

import java.util.Map;

import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

@Path("/hourglass")
public class HourglassResource {

    @Inject
    private HourglassService hourglassService;

    @POST
    @Path("analyze")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response generateMapping(HourglassInput input) {
        if (input == null || input.getDomain() == null || input.getDomain().isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "field 'domain' is required")).build();
        }
        try {
            return Response.ok(hourglassService.process(input)).build();
        } catch (Exception e) {
            return Response.status(Response.Status.BAD_GATEWAY)
                    .entity(Map.of("error", "LLM call failed: " + e.getMessage())).build();
        }
    }
}
