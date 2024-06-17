import React, { useState } from 'react'

import {
  actions,
  AppStatus,
  thunkActions,
  useAppDispatch,
  useAppSelector,
} from 'store/provider'
import { Header } from 'components/header'
import { Chat } from 'components/chat/chat'
import SearchInput from 'components/search_input'
import { ReactComponent as ChatIcon } from 'images/chat_icon.svg'
import { ReactComponent as Logo } from 'images/512.svg'
import { SearchResults } from './components/search_results'

const App = () => {
  const dispatch = useAppDispatch()
  const status = useAppSelector((state) => state.status)
  const sources = useAppSelector((state) => state.sources)
  const [summary, ...messages] = useAppSelector((state) => state.conversation)
  const hasSummary = useAppSelector(
    (state) => !!state.conversation?.[0]?.content
  )
  const [searchQuery, setSearchQuery] = useState<string>('')

  const handleSearch = (query: string) => {
    dispatch(thunkActions.search(query))
  }
  const handleSendChatMessage = (query: string) => {
    dispatch(thunkActions.askQuestion(query))
  }
  const handleAbortRequest = () => {
    dispatch(thunkActions.abortRequest())
  }
  const handleToggleSource = (name) => {
    dispatch(actions.sourceToggle({ name }))
  }
  const handleSourceClick = (name) => {
    dispatch(actions.sourceToggle({ name, expanded: true }))

    setTimeout(() => {
      document
        .querySelector(`[data-source="${name}"]`)
        ?.scrollIntoView({ behavior: 'smooth' })
    }, 300)
  }

  const suggestedQueries = [
    "요즘 NVIDA의 주가가 계속 오르는 이유가 뭐야?",
    "삼성전자의 주요 사업 부문에 대해서 설명해줘",
    "2024년 6월 13일 sk하이닉스의 종가가 얼마야?",
    "AMD의 최근 실적에 대해서 알려줘",
  ]

  return (
    <>
      <Header />

      <div className="p-4 max-w-2xl mx-auto">
        <SearchInput
          onSearch={handleSearch}
          value={searchQuery}
          appStatus={status}
        />

        {status === AppStatus.Idle ? (
          <div className="mx-auto my-6">
            <h2 className="text-zinc-400 text-sm font-medium mb-3  inline-flex items-center gap-2">
              <ChatIcon /> Common questions
            </h2>
            <div className="flex flex-col space-y-4">
              {suggestedQueries.map((query) => (
                <button
                  key={query}
                  className="hover:-translate-y-1 hover:shadow-lg hover:bg-zinc-300 transition-transform h-12 px-4 py-2 bg-zinc-200 rounded-md shadow flex items-center text-zinc-700"
                  onClick={(e) => {
                    e.preventDefault()
                    setSearchQuery(query)
                    handleSearch(query)
                  }}
                >
                  {query}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {hasSummary ? (
              <div className="max-w-2xl mx-auto relative">
                <Chat
                  status={status}
                  messages={messages}
                  summary={summary}
                  onSend={handleSendChatMessage}
                  onAbortRequest={handleAbortRequest}
                  onSourceClick={handleSourceClick}
                />

                <SearchResults
                  results={sources}
                  toggleSource={handleToggleSource}
                />
              </div>
            ) : (
              <div className="h-36 p-6 bg-white rounded-md shadow flex flex-col justify-start items-center gap-4 mt-6">
                <Logo className="w-16 h-16" />
                <p className="text-center text-zinc-400 text-sm ">
                  검색 중입니다...
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </>
  )
}

export default App
