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
              <div className='w-4 h-4 bg-[#27272a] rounded'></div>
              <div className='h-4 bg-[#27272a] rounded flex-1'></div>
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
            placeholder='Add a task...'
            className='flex-1 px-3 py-2 border border-[#27272a] rounded-lg bg-[#18181b] text-[#e4e4e7] text-sm placeholder:text-[#52525b] focus:outline-none focus:ring-2 focus:ring-[#6366f1] focus:border-transparent'
            disabled={isAdding}
          />
          <button
            type='submit'
            disabled={isAdding || !newTodoText.trim()}
            className='px-4 py-2 bg-[#6366f1] text-white rounded-lg hover:bg-[#5558e3] disabled:opacity-40 disabled:cursor-not-allowed transition-all text-sm font-medium'
          >
            Add
          </button>
        </div>
      </form>

      <div className='space-y-1.5 max-h-64 overflow-y-auto'>
        {todos.length === 0 ? (
          <p className='text-[#71717a] text-sm text-center py-4'>
            No tasks yet
          </p>
        ) : (
          todos.map((todo) => (
            <div
              key={todo.id}
              className='flex items-center gap-3 p-2 hover:bg-[#18181b] rounded-lg transition-colors group'
            >
              <input
                type='checkbox'
                checked={todo.done}
                onChange={(e) => onToggle(todo.id, e.target.checked)}
                className='w-4 h-4 cursor-pointer accent-[#6366f1]'
              />
              <span
                className={`flex-1 text-sm ${
                  todo.done ? 'line-through text-[#52525b]' : 'text-[#e4e4e7]'
                }`}
              >
                {todo.text}
              </span>
              <button
                onClick={() => onDelete(todo.id)}
                className='text-[#dc2626] hover:text-[#ef4444] opacity-0 group-hover:opacity-100 transition-all text-lg leading-none'
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
