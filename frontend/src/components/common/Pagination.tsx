import { ReactNode } from 'react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

  const pages = [];
  const maxVisible = 5;

  // Generate page numbers
  let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
  let endPage = Math.min(totalPages, startPage + maxVisible - 1);

  if (endPage - startPage + 1 < maxVisible) {
    startPage = Math.max(1, endPage - maxVisible + 1);
  }

  for (let i = startPage; i <= endPage; i++) {
                pages.push(i);
            }
          }

          if (totalPages <= 1) return null;

          return (
            <nav className="flex items-center justify-center gap-1">
              <button
                onClick={() => onPageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded"
              >
                Prev
              </button>
              <button
                onClick={() => onPageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-100 rounded"
              >
                Next
              </button>
            </nav>
          </div>
        </div>
      </div>
    );
  }
