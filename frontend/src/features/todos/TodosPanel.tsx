import React, { useState } from 'react';
import Card from '../../components/Card';
import type { Todo } from '../../lib/types';

interface TodosPanelProps {
  todos: Todo[];
  loading?: boolean;
  onAdd: (text: string) => Promise<void>;
  onToggle: (id: string, done: boolean) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export const TodosPanel: React.FC<TodosPanelProps> = ({
  todos,
  loading = false,
  onAdd,
  onToggle,
  onDelete,
}) => {
  const [newTodoText, setNewTodoText] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTodoText.trim() || isAdding) return;

    setIsAdding(true);
    try {
      await onAdd(newTodoText.trim());
      setNewTodoText('');
    } finally {
      setIsAdding(false);
    }
  };

  if (loading) {
    return (
      <Card title='To-Do' className='h-full'>
        <div className='space-y-2'>
          {[1, 2, 3].map((i) => (
            <div key={i} className='animate-pulse flex items-center gap-2'>
              <div className='w-4 h-4 bg-gray-300 dark:bg-gray-600 rounded'></div>
              <div className='h-4 bg-gray-300 dark:bg-gray-600 rounded flex-1'></div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card title='To-Do' className='h-full'>
      <form onSubmit={handleAdd} className='mb-4'>
        <div className='flex gap-2'>
          <input
            type='text'
            value={newTodoText}
            onChange={(e) => setNewTodoText(e.target.value)}
            placeholder='Add a new task...'
            className='flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100'
            disabled={isAdding}
          />
          <button
            type='submit'
            disabled={isAdding || !newTodoText.trim()}
            className='px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors'
          >
            Add
          </button>
        </div>
      </form>

      <div className='space-y-2 max-h-64 overflow-y-auto'>
        {todos.length === 0 ? (
          <p className='text-gray-500 dark:text-gray-400 text-sm'>
            No tasks yet
          </p>
        ) : (
          todos.map((todo) => (
            <div
              key={todo.id}
              className='flex items-center gap-2 p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded transition-colors group'
            >
              <input
                type='checkbox'
                checked={todo.done}
                onChange={(e) => onToggle(todo.id, e.target.checked)}
                className='w-4 h-4 cursor-pointer'
              />
              <span
                className={`flex-1 ${
                  todo.done
                    ? 'line-through text-gray-500 dark:text-gray-500'
                    : ''
                }`}
              >
                {todo.text}
              </span>
              <button
                onClick={() => onDelete(todo.id)}
                className='text-red-600 hover:text-red-700 opacity-0 group-hover:opacity-100 transition-opacity'
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>
    </Card>
  );
};

export default TodosPanel;
