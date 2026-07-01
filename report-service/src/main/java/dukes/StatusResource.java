/********************************************************************************
 * CoreFleet — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes;

import java.util.Map;

import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import org.eclipse.microprofile.config.inject.ConfigProperty;

/** Health/readiness probe. Reports the configured model and whether a key is set
 *  — never the key itself. */
@Path("/status")
public class StatusResource {

    @Inject
    @ConfigProperty(name = "openai.model-name", defaultValue = "gpt-4o-mini")
    String modelName;

    @Inject
    @ConfigProperty(name = "openai.api-key", defaultValue = "")
    String apiKey;

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public Map<String, Object> status() {
        return Map.of(
                "status", "up",
                "service", "corefleet-report",
                "model", modelName,
                "keyConfigured", apiKey != null && !apiKey.isBlank());
    }
}
