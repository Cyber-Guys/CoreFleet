/********************************************************************************
 * CoreFleet SDV — based on the Eclipse o-cei hourglass-template (EPL-2.0).
 ********************************************************************************/
package dukes.ai;

import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.service.AiServices;
import dukes.fleet.DriverReportAiService;
import dukes.hourglass.HourglassAiService;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.inject.Produces;
import jakarta.inject.Inject;

/**
 * Builds the typed langchain4j AI services. Each declares a prompt contract and
 * a POJO return type; langchain4j drives the model to emit matching structured
 * JSON and deserializes it.
 */
@ApplicationScoped
public class AiServiceFactory {

    @Inject
    ChatModel chatModel;

    @Produces
    @ApplicationScoped
    public HourglassAiService hourglassAiService() {
        return AiServices.create(HourglassAiService.class, chatModel);
    }

    @Produces
    @ApplicationScoped
    public DriverReportAiService driverReportAiService() {
        return AiServices.create(DriverReportAiService.class, chatModel);
    }
}
