from shared_kernel.config import Config

config = Config()


class SchemaOnboardingEventRegistry:
    # Sync events to master service for schema onboarding tracker operations
    
    # Template Management
    CREATE_TEMPLATE = (
        config.get("MASTER_SERVICE_BASE_ENDPOINT")
        + "/event/subscribe-sync-event/CREATE_SCHEMA_ONBOARDING_TEMPLATE/"
    )

    GET_TEMPLATE = (
        config.get("MASTER_SERVICE_BASE_ENDPOINT")
        + "/event/subscribe-sync-event/GET_SCHEMA_ONBOARDING_TEMPLATE/"
    )

    # Run Management
    CREATE_RUN = (
        config.get("MASTER_SERVICE_BASE_ENDPOINT")
        + "/event/subscribe-sync-event/CREATE_SCHEMA_ONBOARDING_RUN/"
    )

    UPDATE_RUN_STATUS = (
        config.get("MASTER_SERVICE_BASE_ENDPOINT")
        + "/event/subscribe-sync-event/UPDATE_SCHEMA_ONBOARDING_RUN_STATUS/"
    )

    GET_RUN = (
        config.get("MASTER_SERVICE_BASE_ENDPOINT")
        + "/event/subscribe-sync-event/GET_SCHEMA_ONBOARDING_RUN/"
    )

    # Task Management
    CREATE_SINGLE_TASK = (
        config.get("MASTER_SERVICE_BASE_ENDPOINT")
        + "/event/subscribe-sync-event/CREATE_SCHEMA_ONBOARDING_SINGLE_TASK/"
    )

    UPDATE_TASK_STATUS = (
        config.get("MASTER_SERVICE_BASE_ENDPOINT")
        + "/event/subscribe-sync-event/UPDATE_SCHEMA_ONBOARDING_TASK_STATUS/"
    )

    INCREMENT_TASK_ATTEMPTS = (
        config.get("MASTER_SERVICE_BASE_ENDPOINT")
        + "/event/subscribe-sync-event/INCREMENT_SCHEMA_ONBOARDING_TASK_ATTEMPTS/"
    )

    GET_TASK = (
        config.get("MASTER_SERVICE_BASE_ENDPOINT")
        + "/event/subscribe-sync-event/GET_SCHEMA_ONBOARDING_TASK/"
    )

    GET_TASKS_BY_RUN = (
        config.get("MASTER_SERVICE_BASE_ENDPOINT")
        + "/event/subscribe-sync-event/GET_SCHEMA_ONBOARDING_TASKS_BY_RUN/"
    )

    # Note: Next task determination and utility methods are now handled client-side
    # The following events are no longer needed as the logic is implemented locally:
    # - GET_NEXT_ELIGIBLE_TASKS
    # - GET_INITIAL_TASKS  
    # - IS_RUN_COMPLETE
    # - GET_RUN_SUMMARY
