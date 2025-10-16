GITHUB_REPOSITORIES_QUERY: str = """
query GithubRepositories {
  githubRepositories {
    __typename
    ... on GithubRepositories {
      repositories {
        id
        githubOrgName
        githubRepoName
        baseHost
        containerImageId
        createdAt
        updatedAt
      }
    }
    ... on Error {
      message
    }
  }
}
"""


EVENTS_FOR_CHAT_QUERY: str = """query EventsForChat($chatUuid: UUID!) {
  eventsForChat(chatUuid: $chatUuid) {
    ... on EventHistory {
      events {
        ... on UserEvent {
          uuid
          parentUuid
          chatId
          isSidechain
          version
          createdAt
          sidechainRootUuid
          synthetic
          messageData: message {
            ... on TextMessage {
              text
            }
            ... on ToolCallMessage {
              messageId
              toolUseId
              toolName
              toolInput {
                ... on BashToolInput {
                  command
                }
                ... on ReadToolInput {
                  filePath
                }
              }
            }
            ... on ToolResultMessage {
              messageId
              toolUseId
              text
              resultData {
                ... on BashToolResult {
                  shellOutput
                  exitCode
                }
                ... on ReadToolResult {
                  content
                }
              }
            }
          }
        }
        ... on AssistantEvent {
          uuid
          parentUuid
          chatId
          isSidechain
          version
          createdAt
          sidechainRootUuid
          synthetic
          messageData: message {
            ... on TextMessage {
              text
            }
            ... on ToolCallMessage {
              messageId
              toolUseId
              toolName
              toolInput {
                ... on BashToolInput {
                  command
                }
                ... on ReadToolInput {
                  filePath
                }
              }
            }
          }
        }
        ... on SystemEvent {
          uuid
          parentUuid
          chatId
          isSidechain
          version
          createdAt
          sidechainRootUuid
          messageData: message {
            ... on ToolCallMessage {
              messageId
              toolUseId
              toolName
              toolInput {
                ... on BashToolInput {
                  command
                }
                ... on ReadToolInput {
                  filePath
                }
              }
            }
            ... on ToolResultMessage {
              messageId
              toolUseId
              text
              resultData {
                ... on BashToolResult {
                  shellOutput
                  exitCode
                }
                ... on ReadToolResult {
                  content
                }
              }
            }
            ... on ToolExecutionStatusMessage {
              executionStatus: status
            }
            ... on ToolPermissionStatusMessage {
              permissionStatus: status
            }
          }
        }
      }
    }
  }
}
"""
