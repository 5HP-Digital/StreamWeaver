FROM mcr.microsoft.com/dotnet/runtime:9.0 AS base
USER $APP_UID
WORKDIR /app

FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
ARG BUILD_CONFIGURATION=Release
WORKDIR /src
COPY ["IPTV.JobWorker.csproj", "IPTV.JobWorker/"]
RUN dotnet restore "IPTV.JobWorker/IPTV.JobWorker.csproj"
COPY . IPTV.JobWorker/
WORKDIR "/src/IPTV.JobWorker"
RUN dotnet build "./IPTV.JobWorker.csproj" -c $BUILD_CONFIGURATION -o /app/build

FROM build AS publish
ARG BUILD_CONFIGURATION=Release
RUN dotnet publish "./IPTV.JobWorker.csproj" -c $BUILD_CONFIGURATION -o /app/publish /p:UseAppHost=false

FROM base AS final
ENV CONFIG_DIR=/config
WORKDIR /app
COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "IPTV.JobWorker.dll"]
