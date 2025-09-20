import React from 'react';
import type { NewsCategory, CategoryFilterItem } from '../types/news';

interface CategoryFilterProps {
  categories: CategoryFilterItem[];
  selectedCategory: NewsCategory | 'all';
  onCategoryChange: (category: NewsCategory | 'all') => void;
}

const CategoryFilter: React.FC<CategoryFilterProps> = ({
  categories,
  selectedCategory,
  onCategoryChange
}) => {
  return (
    <div className="category-filter">
      <button
        className={`filter-button ${selectedCategory === 'all' ? 'active' : ''}`}
        onClick={() => onCategoryChange('all')}
      >
        All Categories
      </button>
      {categories.map((category) => (
        <button
          key={category.category}
          className={`filter-button ${selectedCategory === category.category ? 'active' : ''}`}
          style={{
            backgroundColor: selectedCategory === category.category ? category.color : 'transparent',
            borderColor: category.color,
            color: selectedCategory === category.category ? 'white' : category.color
          }}
          onClick={() => onCategoryChange(category.category)}
        >
          {category.label}
        </button>
      ))}
    </div>
  );
};

export default CategoryFilter;