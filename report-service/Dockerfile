# --- build stage: compile the WAR ---
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /build
COPY pom.xml .
# warm the dependency cache (best-effort; ignored if offline)
RUN mvn -q -B dependency:go-offline 2>/dev/null || true
COPY src ./src
RUN mvn -q -B clean package

# --- runtime stage: deploy on Open Liberty (java17 = newest official tag) ---
FROM open-liberty:full-java17-openj9

COPY --chown=1001:0 src/main/liberty/config/server.xml /config/server.xml
COPY --chown=1001:0 --from=build /build/target/corefleet-report.war /config/apps/

# OPENAI_API_KEY is supplied at runtime (env / compose), never baked in.
EXPOSE 8080
RUN configure.sh
