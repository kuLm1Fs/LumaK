export {
  buildChatPayload,
  buildProjectSwitchPayload,
  normalizeTodoTasks,
} from "../../shared/gateway-contract.js";
export type {
  ChatPayload as GatewayChatPayload,
  GatewayMessage,
  ProjectSwitchPayload as GatewayProjectSwitchPayload,
  ProviderConfig,
  TodoTask,
  TodoTaskSource,
  TodoTaskStatus,
} from "../../shared/gateway-contract.js";
