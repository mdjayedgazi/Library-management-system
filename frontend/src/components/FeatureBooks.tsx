import { useEffect, useState } from 'react'
import { baseUel } from '../servies/BaseUel.tsx'
import type { Book } from '../type.ts'
import BookCard from './BookCard.tsx'

const FeatureBooks = () => {
  const [featureBooks, setFeatureBooks] = useState<Book[]>([])

  useEffect(() => {
    fetch(`${baseUel}/books/all`)
      .then((res) => res.json())
      .then((data) => setFeatureBooks(data))
  }, [])
  return (
    <>
      <div className="flex mt-5 flex-col items-center justify-between">
        <h1 className={'font-bold text-4xl '}>Our Featured Books</h1>
      </div>
      <div className="grid mt-5 w-full grid-cols-2 gap-3 px-10 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 md:gap-4">
        {featureBooks.slice(0, 6).map((book) => (
          <BookCard key={book.id} book={book} />
        ))}
      </div>
    </>
  )
}

export default FeatureBooks
