import React from 'react';
import Card from '../../components/Card';
import type { NewsItem } from '../../lib/types';

interface NewsPanelProps {
  items: NewsItem[];
  loading?: boolean;
}

export const NewsPanel: React.FC<NewsPanelProps> = ({
  items,
  loading = false,
}) => {
  if (loading) {
    return (
      <Card title='News' className='h-full'>
        <div className='space-y-3'>
          {[1, 2, 3].map((i) => (
            <div key={i} className='animate-pulse'>
              <div className='h-4 bg-gray-300 dark:bg-gray-600 rounded w-full mb-2'></div>
              <div className='h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/3'></div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card title='News' className='h-full'>
      {items.length === 0 ? (
        <p className='text-gray-500 dark:text-gray-400'>No news available</p>
      ) : (
        <div className='space-y-3 max-h-96 overflow-y-auto'>
          {items.map((item) => (
            <a
              key={item.id}
              href={item.url}
              target='_blank'
              rel='noopener noreferrer'
              className='block hover:bg-gray-50 dark:hover:bg-gray-700 p-2 rounded transition-colors'
            >
              <h4 className='font-medium text-sm leading-tight mb-1'>
                {item.title}
              </h4>
              <div className='flex justify-between items-center text-xs text-gray-500 dark:text-gray-500'>
                <span>{item.source}</span>
                <span>{new Date(item.publishedISO).toLocaleDateString()}</span>
              </div>
            </a>
          ))}
        </div>
      )}
    </Card>
  );
};

export default NewsPanel;
