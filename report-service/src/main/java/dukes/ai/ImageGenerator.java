/********************************************************************************
 * CoreFleet, based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.ai;

import java.io.StringReader;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.logging.Logger;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.json.Json;
import jakarta.json.JsonArray;
import jakarta.json.JsonObject;
import jakarta.json.JsonReader;
import jakarta.json.JsonValue;
import org.eclipse.microprofile.config.inject.ConfigProperty;

/**
 * Generates an image with the image_generation tool of the OpenAI Responses API
 * (POST /v1/responses with tools:[{type:"image_generation"}]), like the
 * reference script. The key we use cannot call /images/generations, the
 * endpoint langchain4j uses, so this goes through /v1/responses.
 *
 * Returns a data: URI (base64 PNG), or null on failure. A report without an
 * image is still valid.
 */
@ApplicationScoped
public class ImageGenerator {

    private static final Logger LOG = Logger.getLogger(ImageGenerator.class.getName());

    @Inject
    @ConfigProperty(name = "openai.api-key", defaultValue = "")
    String apiKey;

    @Inject
    @ConfigProperty(name = "openai.base-url", defaultValue = "https://api.openai.com/v1")
    String baseUrl;

    @Inject
    @ConfigProperty(name = "openai.image-model", defaultValue = "gpt-5-mini")
    String imageModel;

    @Inject
    @ConfigProperty(name = "openai.image-enabled", defaultValue = "true")
    boolean enabled;

    @Inject
    @ConfigProperty(name = "openai.image-timeout-seconds", defaultValue = "240")
    int timeoutSeconds;

    // lower quality = faster; size must be a valid gpt-image-1 value
    @Inject
    @ConfigProperty(name = "openai.image-size", defaultValue = "1024x1024")
    String imageSize;

    @Inject
    @ConfigProperty(name = "openai.image-quality", defaultValue = "low")
    String imageQuality;

    public boolean isEnabled() {
        return enabled && apiKey != null && !apiKey.isBlank();
    }

    // force HTTP/1.1: on OpenJ9 the default HTTP/2 client hangs when talking
    // to OpenAI, HTTP/1.1 works
    private final HttpClient http = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .connectTimeout(Duration.ofSeconds(15))
            .build();

    private static final int MAX_ATTEMPTS = 3;

    public String generate(String prompt) {
        if (!enabled || apiKey == null || apiKey.isBlank()) return null;

        String body = Json.createObjectBuilder()
                .add("model", imageModel)
                .add("input", prompt)
                .add("tools", Json.createArrayBuilder()
                        .add(Json.createObjectBuilder()
                                .add("type", "image_generation")
                                .add("size", imageSize)
                                .add("quality", imageQuality)))
                // make the model call the image tool every time
                .add("tool_choice", Json.createObjectBuilder().add("type", "image_generation"))
                .build().toString();

        // image_generation is slow (~60-90s) and OpenAI sometimes returns a
        // temporary 5xx, so retry those.
        for (int attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
            try {
                HttpRequest req = HttpRequest.newBuilder()
                        .uri(URI.create(baseUrl + "/responses"))
                        .timeout(Duration.ofSeconds(timeoutSeconds))
                        .header("Authorization", "Bearer " + apiKey)
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(body))
                        .build();

                HttpResponse<String> resp = http.send(req, HttpResponse.BodyHandlers.ofString());
                int sc = resp.statusCode();
                if (sc / 100 == 2) {
                    String img = extractImage(resp.body());
                    if (img != null) return img;
                    return null; // 2xx but no image -> don't retry
                }
                if (sc / 100 == 5) {
                    LOG.warning("image generation HTTP " + sc + " (attempt " + attempt + "/" + MAX_ATTEMPTS + ")");
                    backoff(attempt);
                    continue; // transient upstream error -> retry
                }
                String snippet = resp.body() == null ? "" : resp.body().substring(0, Math.min(200, resp.body().length()));
                LOG.warning("image generation HTTP " + sc + " (giving up): " + snippet);
                return null; // 4xx -> not retryable
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return null;
            } catch (Exception e) {
                LOG.warning("image generation error (attempt " + attempt + "): " + e.getMessage());
                backoff(attempt);
            }
        }
        return null;
    }

    private static String extractImage(String responseBody) {
        try (JsonReader r = Json.createReader(new StringReader(responseBody))) {
            JsonObject root = r.readObject();
            if (!root.containsKey("output") || root.isNull("output")) return null;
            JsonArray output = root.getJsonArray("output");
            for (JsonValue v : output) {
                if (v.getValueType() != JsonValue.ValueType.OBJECT) continue;
                JsonObject o = v.asJsonObject();
                if ("image_generation_call".equals(o.getString("type", ""))
                        && o.containsKey("result") && !o.isNull("result")) {
                    return "data:image/png;base64," + o.getString("result");
                }
            }
        } catch (Exception ignored) {
            // fall through
        }
        return null;
    }

    private static void backoff(int attempt) {
        try {
            Thread.sleep(1500L * attempt);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
