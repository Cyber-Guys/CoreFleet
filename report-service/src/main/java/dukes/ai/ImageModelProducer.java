/********************************************************************************
 * CoreFleet SDV — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.ai;

import java.time.Duration;

import dev.langchain4j.model.image.ImageModel;
import dev.langchain4j.model.openai.OpenAiImageModel;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.inject.Produces;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;

/**
 * Produces the langchain4j {@link OpenAiImageModel} (DALL·E) used to render a
 * visual of the Hourglass Model for a driver report. Same key as the chat model.
 */
@ApplicationScoped
public class ImageModelProducer {

    @Inject
    @ConfigProperty(name = "openai.api-key", defaultValue = "")
    String apiKey;

    @Inject
    @ConfigProperty(name = "openai.base-url", defaultValue = "https://api.openai.com/v1")
    String baseUrl;

    @Inject
    @ConfigProperty(name = "openai.image-model", defaultValue = "dall-e-3")
    String imageModelName;

    @Inject
    @ConfigProperty(name = "openai.image-timeout-seconds", defaultValue = "90")
    int timeoutSeconds;

    @Produces
    @ApplicationScoped
    public ImageModel imageModel() {
        return OpenAiImageModel.builder()
                .apiKey(apiKey == null || apiKey.isBlank() ? "missing-OPENAI_API_KEY" : apiKey)
                .baseUrl(baseUrl)
                .modelName(imageModelName)
                .timeout(Duration.ofSeconds(timeoutSeconds))
                .build();
    }
}
