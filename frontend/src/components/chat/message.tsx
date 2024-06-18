import React from 'react'
import { ChatMessageType, SourceType } from 'types'
import { Loader } from 'components/loader'
import { Sources } from 'components/chat/sources'
import { ReactComponent as UserLogo } from 'images/user.svg'
import AILogo from 'images/512.png'

type ChatMessageProps = Omit<ChatMessageType, 'id'> & {
  onSourceClick: (source: string) => void
}
export const ChatMessage: React.FC<ChatMessageProps> = ({
  content,
  isHuman,
  sources,
  evalScores,
  loading,
  onSourceClick,
}) => {
  const messageIcon = isHuman ? (
    <span className="self-end p-2 rounded-md border border-zind-200 bg-white">
      <UserLogo width={24} height={24} />
    </span>
  ) : (
    <span className="self-end p-2 rounded-md bg-blue-50 shadow">
      <img src={AILogo} alt="AI Logo" width={24} height={24} />
    </span>
  )

  return (
    <div>
      <div className={`flex mt-6 gap-2 ${isHuman ? 'justify-end' : ''}`}>
        {messageIcon}

        <div
          className={`w-96 p-4 rounded-md ${
            isHuman
              ? 'rounded-br-none text-white bg-blue-500 -order-1'
              : 'bg-white shadow border-2 border-blue-100 rounded-bl-none text-zinc-700'
          }`}
        >
          <span
            className="whitespace-pre-wrap leading-normal"
            dangerouslySetInnerHTML={{ __html: content || '' }}
          ></span>
          {loading && <Loader />}
        </div>
      </div>
      {!isHuman && evalScores && (
        <div className={`flex mt-2 gap-2 ${isHuman ? 'justify-end' : ''}`}>
          {messageIcon}
          <div
            className={`w-96 p-4 rounded-md ${
              isHuman
                ? 'rounded-br-none text-white bg-blue-500 -order-1'
                : 'bg-white shadow border-2 border-blue-100 rounded-bl-none text-zinc-700'
            }`}
          >
            <span className="font-bold">Evaluation</span>
            <div className="whitespace-pre-wrap leading-normal">
              {Object.entries(evalScores).map(([key, value]) => (
                <div key={key}>
                  {key}: {value}
                  <br />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      {!!sources?.length && (
        <div className="mt-6 gap-2 inline-flex">
          {messageIcon}
          <Sources sources={sources || []} onSourceClick={onSourceClick} />
        </div>
      )}
    </div>
  )
}
