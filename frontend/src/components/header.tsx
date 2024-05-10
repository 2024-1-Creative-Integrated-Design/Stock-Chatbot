import TypeMark from 'images/TypeMark.png'

export const Header = () => (
  <div className="flex flex-row justify-between space-x-6 px-8 py-3.5 bg-black w-full">
    <div className="pr-8 border-r border-ink">
      <a href="/">
        <img width={240} height={80} src={TypeMark} alt="Logo" />
      </a>
    </div>
  </div>
)
