import type { Book } from '../type.ts'

type BookCardProps = {
  book: Book
}

const BookCard = ({ book }: BookCardProps) => {
  return (
    <article className="group flex h-full min-w-0 flex-col overflow-hidden rounded-xl border border-base-300/70 bg-base-100 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:border-base-300 hover:shadow-md">
      {/* Book Cover */}
      <div className="flex h-56 items-center justify-center bg-base-200/40 px-3 py-3">
        <img
          src={book.cover_image}
          alt={book.title}
          loading="lazy"
          className="h-full max-w-full rounded-md object-contain shadow-sm transition-transform duration-300 group-hover:scale-[1.03]"
        />
      </div>

      {/* Book Information */}
      <div className="flex flex-1 flex-col p-3">
        {/* Category */}
        <div className="mb-2 flex items-center justify-between gap-2">
          <span className="truncate text-xs font-medium capitalize text-base-content/60">
            {book.category.replaceAll('_', ' ')}
          </span>

          <span
            className={`shrink-0 text-xs font-medium ${
              book.available_copies > 0 ? 'text-success' : 'text-error'
            }`}
          >
            {book.available_copies > 0 ? 'In Stock' : 'Unavailable'}
          </span>
        </div>

        {/* Title */}
        <h2 className="line-clamp-2 min-h-11 text-sm font-bold leading-5">{book.title}</h2>

        {/* Author */}
        <p className="mt-1 truncate text-xs text-base-content/60">By {book.author}</p>

        {/* Description */}
        <p className="mt-2 line-clamp-2 text-xs leading-5 text-base-content/65">
          {book.description}
        </p>

        {/* Price and Availability */}
        <div className="mt-auto pt-3">
          <div className="mb-3 border-t border-base-300/70" />

          <div className="flex items-center justify-between gap-2">
            <div>
              <p className="text-[11px] text-base-content/50">Price</p>
              <p className="text-lg font-bold text-primary">
                ৳{book.price.toLocaleString('en-BD')}
              </p>
            </div>

            <div className="text-right">
              <p className="text-[11px] text-base-content/50">Available</p>
              <p className="text-sm font-semibold">
                {book.available_copies}/{book.total_copies}
              </p>
            </div>
          </div>
        </div>
      </div>
    </article>
  )
}

export default BookCard
