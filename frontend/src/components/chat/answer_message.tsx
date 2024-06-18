import { Sources } from './sources'
import { ChatMessageType } from '../../types'

interface AnswerMessageProps {
  text: ChatMessageType['content']
  sources: ChatMessageType['sources']
  evalScores: ChatMessageType['evalScores']
  onSourceClick: (source: string) => void
}

export const AnswerMessage: React.FC<AnswerMessageProps> = ({
  text,
  sources,
  evalScores,
  onSourceClick,
}) => {
  return (
    <div className="mb-4">
      <header className="flex flex-row justify-between mb-8">
        <div className="flex flex-row justify-center align-middle items-center">
          <div className="flex flex-col justify-start">
            <h2 className="text-zinc-700 text-2xl font-bold leading-9">
              Answer
            </h2>
          </div>
        </div>
      </header>

      {text && (
        <div
          className="text-base leading-tight text-gray-800 whitespace-pre-wrap mb-8"
          dangerouslySetInnerHTML={{ __html: text }}
        ></div>
      )}
      {evalScores && (
        <div className="mb-4">
          <span className="font-bold">Evaluation</span>
          <div>
            {Object.entries(evalScores).map(([key, value]) => (
              <div key={key}>
                {key}: {value}
                <br />
              </div>
            ))}
          </div>
        </div>
      )}
      {sources && (
        <Sources
          showDisclaimer
          sources={sources}
          onSourceClick={onSourceClick}
        />
      )}
    </div>
  )
}
