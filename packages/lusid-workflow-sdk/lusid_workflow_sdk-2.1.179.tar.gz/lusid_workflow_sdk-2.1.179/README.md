<a id="documentation-for-api-endpoints"></a>
## Documentation for API Endpoints

All URIs are relative to *https://fbn-prd.lusid.com/workflow*

Class | Method | HTTP request | Description
------------ | ------------- | ------------- | -------------
*ActionLogsApi* | [**get_action_logs**](docs/ActionLogsApi.md#get_action_logs) | **GET** /api/actionlogs/{id} | [EXPERIMENTAL] GetActionLogs: Get the Action Logs for an Action Id
*ApplicationMetadataApi* | [**list_access_controlled_resources**](docs/ApplicationMetadataApi.md#list_access_controlled_resources) | **GET** /api/metadata/access/resources | ListAccessControlledResources: Get resources available for access control
*EventHandlersApi* | [**create_event_handler**](docs/EventHandlersApi.md#create_event_handler) | **POST** /api/eventhandlers | [EXPERIMENTAL] CreateEventHandler: Create a new Event Handler
*EventHandlersApi* | [**delete_event_handler**](docs/EventHandlersApi.md#delete_event_handler) | **DELETE** /api/eventhandlers/{scope}/{code} | [EXPERIMENTAL] DeleteEventHandler: Delete an Event Handler
*EventHandlersApi* | [**get_event_handler**](docs/EventHandlersApi.md#get_event_handler) | **GET** /api/eventhandlers/{scope}/{code} | [EXPERIMENTAL] GetEventHandler: Get an Event Handler
*EventHandlersApi* | [**list_event_handlers**](docs/EventHandlersApi.md#list_event_handlers) | **GET** /api/eventhandlers | [EXPERIMENTAL] ListEventHandlers: List Event Handlers
*EventHandlersApi* | [**update_event_handler**](docs/EventHandlersApi.md#update_event_handler) | **PUT** /api/eventhandlers/{scope}/{code} | [EXPERIMENTAL] UpdateEventHandler: Update an existing Event handler
*TaskDefinitionsApi* | [**create_task_definition**](docs/TaskDefinitionsApi.md#create_task_definition) | **POST** /api/taskdefinitions | CreateTaskDefinition: Create a new Task Definition
*TaskDefinitionsApi* | [**delete_task_definition**](docs/TaskDefinitionsApi.md#delete_task_definition) | **DELETE** /api/taskdefinitions/{scope}/{code} | DeleteTaskDefinition: Delete a Task Definition
*TaskDefinitionsApi* | [**get_task_definition**](docs/TaskDefinitionsApi.md#get_task_definition) | **GET** /api/taskdefinitions/{scope}/{code} | GetTaskDefinition: Get a Task Definition
*TaskDefinitionsApi* | [**list_task_definitions**](docs/TaskDefinitionsApi.md#list_task_definitions) | **GET** /api/taskdefinitions | ListTaskDefinitions: List Task Definitions
*TaskDefinitionsApi* | [**list_tasks_for_task_definition**](docs/TaskDefinitionsApi.md#list_tasks_for_task_definition) | **GET** /api/taskdefinitions/{scope}/{code}/tasks | ListTasksForTaskDefinition: List Tasks for a Task Definition
*TaskDefinitionsApi* | [**update_task_definition**](docs/TaskDefinitionsApi.md#update_task_definition) | **PUT** /api/taskdefinitions/{scope}/{code} | UpdateTaskDefinition: Update an existing Task Definition
*TasksApi* | [**batch_update_tasks**](docs/TasksApi.md#batch_update_tasks) | **PATCH** /api/tasks/$update | [EXPERIMENTAL] BatchUpdateTasks: Batch update tasks
*TasksApi* | [**create_task**](docs/TasksApi.md#create_task) | **POST** /api/tasks | CreateTask: Create a new Task
*TasksApi* | [**delete_task**](docs/TasksApi.md#delete_task) | **DELETE** /api/tasks/{id} | DeleteTask: Delete a Task
*TasksApi* | [**delete_tasks**](docs/TasksApi.md#delete_tasks) | **POST** /api/tasks/$delete | DeleteTasks: Batch Delete Tasks
*TasksApi* | [**get_task**](docs/TasksApi.md#get_task) | **GET** /api/tasks/{id} | GetTask: Get a Task
*TasksApi* | [**get_task_history**](docs/TasksApi.md#get_task_history) | **GET** /api/tasks/{id}/history | GetTaskHistory: Get the history of a Task
*TasksApi* | [**list_tasks**](docs/TasksApi.md#list_tasks) | **GET** /api/tasks | ListTasks: List Tasks
*TasksApi* | [**update_task**](docs/TasksApi.md#update_task) | **POST** /api/tasks/{id} | UpdateTask: Update a Task
*WorkersApi* | [**create_worker**](docs/WorkersApi.md#create_worker) | **POST** /api/workers | CreateWorker: Create a new Worker
*WorkersApi* | [**delete_worker**](docs/WorkersApi.md#delete_worker) | **DELETE** /api/workers/{scope}/{code} | DeleteWorker: Delete a Worker
*WorkersApi* | [**get_worker**](docs/WorkersApi.md#get_worker) | **GET** /api/workers/{scope}/{code} | GetWorker: Get a Worker
*WorkersApi* | [**get_worker_result**](docs/WorkersApi.md#get_worker_result) | **GET** /api/workers/{runId}/$result | GetWorkerResult: Get the status of a specific run of a worker with any relevant results
*WorkersApi* | [**list_workers**](docs/WorkersApi.md#list_workers) | **GET** /api/workers | ListWorkers: List Workers
*WorkersApi* | [**run_worker**](docs/WorkersApi.md#run_worker) | **POST** /api/workers/{scope}/{code}/$run | RunWorker: Run a Worker
*WorkersApi* | [**update_worker**](docs/WorkersApi.md#update_worker) | **PUT** /api/workers/{scope}/{code} | UpdateWorker: Update a Worker


<a id="documentation-for-models"></a>
## Documentation for Models

 - [AccessControlledAction](docs/AccessControlledAction.md)
 - [AccessControlledResource](docs/AccessControlledResource.md)
 - [ActionDefinition](docs/ActionDefinition.md)
 - [ActionDefinitionResponse](docs/ActionDefinitionResponse.md)
 - [ActionDetails](docs/ActionDetails.md)
 - [ActionDetailsResponse](docs/ActionDetailsResponse.md)
 - [ActionId](docs/ActionId.md)
 - [ActionLog](docs/ActionLog.md)
 - [ActionLogItem](docs/ActionLogItem.md)
 - [ActionLogOrigin](docs/ActionLogOrigin.md)
 - [BatchUpdateTasksRequest](docs/BatchUpdateTasksRequest.md)
 - [BatchUpdateTasksResponse](docs/BatchUpdateTasksResponse.md)
 - [CalendarReference](docs/CalendarReference.md)
 - [ChangeItem](docs/ChangeItem.md)
 - [CreateChildTaskConfiguration](docs/CreateChildTaskConfiguration.md)
 - [CreateChildTasksAction](docs/CreateChildTasksAction.md)
 - [CreateChildTasksActionResponse](docs/CreateChildTasksActionResponse.md)
 - [CreateEventHandlerRequest](docs/CreateEventHandlerRequest.md)
 - [CreateNewTaskActivity](docs/CreateNewTaskActivity.md)
 - [CreateNewTaskActivityResponse](docs/CreateNewTaskActivityResponse.md)
 - [CreateTaskDefinitionRequest](docs/CreateTaskDefinitionRequest.md)
 - [CreateTaskRequest](docs/CreateTaskRequest.md)
 - [CreateWorkerRequest](docs/CreateWorkerRequest.md)
 - [CutLabelReference](docs/CutLabelReference.md)
 - [DateAdjustment](docs/DateAdjustment.md)
 - [DateRegularity](docs/DateRegularity.md)
 - [DayOfYear](docs/DayOfYear.md)
 - [DayRegularity](docs/DayRegularity.md)
 - [DeleteTasksRequest](docs/DeleteTasksRequest.md)
 - [DeletedEntityResponse](docs/DeletedEntityResponse.md)
 - [ErrorDetail](docs/ErrorDetail.md)
 - [EventHandler](docs/EventHandler.md)
 - [EventHandlerMapping](docs/EventHandlerMapping.md)
 - [EventMatchingPattern](docs/EventMatchingPattern.md)
 - [Fail](docs/Fail.md)
 - [FailResponse](docs/FailResponse.md)
 - [FieldMapping](docs/FieldMapping.md)
 - [GetWorkerResultResponse](docs/GetWorkerResultResponse.md)
 - [GroupReconciliation](docs/GroupReconciliation.md)
 - [GroupReconciliationResponse](docs/GroupReconciliationResponse.md)
 - [HealthCheck](docs/HealthCheck.md)
 - [HealthCheckResponse](docs/HealthCheckResponse.md)
 - [IdSelectorDefinition](docs/IdSelectorDefinition.md)
 - [IdentifierPartSchema](docs/IdentifierPartSchema.md)
 - [InitialState](docs/InitialState.md)
 - [LibraryResponse](docs/LibraryResponse.md)
 - [Link](docs/Link.md)
 - [LuminesceView](docs/LuminesceView.md)
 - [LuminesceViewResponse](docs/LuminesceViewResponse.md)
 - [LusidProblemDetails](docs/LusidProblemDetails.md)
 - [LusidValidationProblemDetails](docs/LusidValidationProblemDetails.md)
 - [PagedResourceListOfEventHandler](docs/PagedResourceListOfEventHandler.md)
 - [PagedResourceListOfTask](docs/PagedResourceListOfTask.md)
 - [PagedResourceListOfTaskDefinition](docs/PagedResourceListOfTaskDefinition.md)
 - [PagedResourceListOfWorker](docs/PagedResourceListOfWorker.md)
 - [Parameter](docs/Parameter.md)
 - [ParameterValue](docs/ParameterValue.md)
 - [ReadOnlyStates](docs/ReadOnlyStates.md)
 - [RecurrencePattern](docs/RecurrencePattern.md)
 - [RelativeMonthRegularity](docs/RelativeMonthRegularity.md)
 - [ResourceId](docs/ResourceId.md)
 - [ResourceListOfAccessControlledResource](docs/ResourceListOfAccessControlledResource.md)
 - [ResourceListOfChangeItem](docs/ResourceListOfChangeItem.md)
 - [ResourceListOfTask](docs/ResourceListOfTask.md)
 - [ResultField](docs/ResultField.md)
 - [ResultMatchingPattern](docs/ResultMatchingPattern.md)
 - [ResultantChildTaskConfiguration](docs/ResultantChildTaskConfiguration.md)
 - [RunWorkerAction](docs/RunWorkerAction.md)
 - [RunWorkerActionResponse](docs/RunWorkerActionResponse.md)
 - [RunWorkerRequest](docs/RunWorkerRequest.md)
 - [RunWorkerResponse](docs/RunWorkerResponse.md)
 - [ScheduleMatchingPattern](docs/ScheduleMatchingPattern.md)
 - [ScheduleMatchingPatternContext](docs/ScheduleMatchingPatternContext.md)
 - [ScheduledTimeAdjustment](docs/ScheduledTimeAdjustment.md)
 - [SchedulerJob](docs/SchedulerJob.md)
 - [SchedulerJobResponse](docs/SchedulerJobResponse.md)
 - [Sleep](docs/Sleep.md)
 - [SleepResponse](docs/SleepResponse.md)
 - [SpecificMonthRegularity](docs/SpecificMonthRegularity.md)
 - [SpecifiedTime](docs/SpecifiedTime.md)
 - [Stack](docs/Stack.md)
 - [Task](docs/Task.md)
 - [TaskActivity](docs/TaskActivity.md)
 - [TaskActivityResponse](docs/TaskActivityResponse.md)
 - [TaskDefinition](docs/TaskDefinition.md)
 - [TaskDefinitionVersion](docs/TaskDefinitionVersion.md)
 - [TaskFieldDefinition](docs/TaskFieldDefinition.md)
 - [TaskInstanceField](docs/TaskInstanceField.md)
 - [TaskStateDefinition](docs/TaskStateDefinition.md)
 - [TaskSummary](docs/TaskSummary.md)
 - [TaskTransitionDefinition](docs/TaskTransitionDefinition.md)
 - [TimeAdjustment](docs/TimeAdjustment.md)
 - [TimeConstraints](docs/TimeConstraints.md)
 - [TimeOfDay](docs/TimeOfDay.md)
 - [TransitionTriggerDefinition](docs/TransitionTriggerDefinition.md)
 - [TriggerParentTaskAction](docs/TriggerParentTaskAction.md)
 - [TriggerParentTaskActionResponse](docs/TriggerParentTaskActionResponse.md)
 - [TriggerSchema](docs/TriggerSchema.md)
 - [UpdateEventHandlerRequest](docs/UpdateEventHandlerRequest.md)
 - [UpdateMatchingTasksActivity](docs/UpdateMatchingTasksActivity.md)
 - [UpdateMatchingTasksActivityResponse](docs/UpdateMatchingTasksActivityResponse.md)
 - [UpdateTaskDefinitionRequest](docs/UpdateTaskDefinitionRequest.md)
 - [UpdateTaskRequest](docs/UpdateTaskRequest.md)
 - [UpdateTaskWithIdAndTriggerRequest](docs/UpdateTaskWithIdAndTriggerRequest.md)
 - [UpdateWorkerRequest](docs/UpdateWorkerRequest.md)
 - [ValueConstraints](docs/ValueConstraints.md)
 - [VersionInfo](docs/VersionInfo.md)
 - [WeekRegularity](docs/WeekRegularity.md)
 - [Worker](docs/Worker.md)
 - [WorkerConfiguration](docs/WorkerConfiguration.md)
 - [WorkerConfigurationResponse](docs/WorkerConfigurationResponse.md)
 - [WorkerStatusTriggers](docs/WorkerStatusTriggers.md)
 - [YearRegularity](docs/YearRegularity.md)

