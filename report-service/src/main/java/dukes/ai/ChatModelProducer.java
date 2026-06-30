/********************************************************************************
 * CoreFleet SDV — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.ai;

import java.time.Duration;

import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.model.openai.OpenAiChatModel;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.inject.Produces;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;

/**
 * Produces the langchain4j {@link ChatModel} from MicroProfile config.
 *
 * The API key is read from {@code openai.api-key}, which MicroProfile Config maps
 * from the {@code OPENAI_API_KEY} environment variable. The key is never compiled
 * into the artifact.
 */
@ApplicationScoped
public class ChatModelProducer {

    @Inject
    @ConfigProperty(name = "openai.api-key", defaultValue = "")
    String apiKey;

    @Inject
    @ConfigProperty(name = "openai.model-name", defaultValue = "gpt-4o-mini")
    String modelName;

    @Inject
    @ConfigProperty(name = "openai.base-url", defaultValue = "https://api.openai.com/v1")
    String baseUrl;

    @Inject
    @ConfigProperty(name = "openai.timeout-seconds", defaultValue = "60")
    int timeoutSeconds;

    @Produces
    @ApplicationScoped
    public ChatModel chatModel() {
        return OpenAiChatModel.builder()
                // a non-blank placeholder keeps the builder happy; a real call
                // with a missing key fails with a clear 401 at request time
                .apiKey(apiKey == null || apiKey.isBlank() ? "missing-OPENAI_API_KEY" : apiKey)
                .baseUrl(baseUrl)
                .modelName(modelName)
                .timeout(Duration.ofSeconds(timeoutSeconds))
                .temperature(0.3)
                .build();
    }
}
