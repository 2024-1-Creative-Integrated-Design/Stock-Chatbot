import React from 'react'

import pdf from 'images/pdf.png'
import dart from 'images/dart.png'
import edgar from 'images/edgar.png'
import news from 'images/news.png'
import stock from 'images/stock.png'

export type SourceIconType = {
  className?: string
  icon:
    | 'news'
    | 'stock'
    | 'dart'
    | 'edgar'
    | string
}
export const SourceIcon: React.FC<SourceIconType> = ({ className, icon }) => {
  const iconNameToImageMap = {
    news,
    stock,
    dart,
    edgar,
  }
  return (
    <span className={className}>
      <img className="w-6 h-6" src={iconNameToImageMap[icon]} alt={icon} />
    </span>
  )
}
