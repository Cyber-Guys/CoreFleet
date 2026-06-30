/********************************************************************************
 * CoreFleet SDV — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.hourglass;

import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;
import dev.langchain4j.service.V;

/**
 * LLM-backed mapping of a domain + use case onto the Eclipse Hourglass Model.
 * langchain4j fills {@link HourglassOutput} from the model's structured response.
 */
public interface HourglassAiService {

    @SystemMessage("""
        You are an enterprise architect. Map the given domain and use case onto the
        Eclipse "Hourglass Model":
          - a wide TOP of stakeholders who depend on the system,
          - a thin WAIST of shared capabilities / standards that everything relies on,
          - a wide BOTTOM of concrete standards groups and building blocks.
        Return concise, concrete lists. Do not add prose or commentary.""")
    @UserMessage("Domain: {{domain}}\nUse case: {{useCase}}")
    HourglassOutput analyze(@V("domain") String domain, @V("useCase") String useCase);
}
