import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Home from '@/app/page'

describe('Home Page', () => {
  it('renders the main heading', () => {
    render(<Home />)
    
    const heading = screen.getByText(/AI-Powered Hotel Intelligence/i)
    expect(heading).toBeInTheDocument()
  })

  it('displays the destination search input and submit button', () => {
    render(<Home />)
    
    const input = screen.getByPlaceholderText(/Where are you traveling/i)
    expect(input).toBeInTheDocument()

    const button = screen.getByRole('button', { name: /Discover Hotels/i })
    expect(button).toBeInTheDocument()
  })

  it('shows production recommendation model cards', () => {
    render(<Home />)
    
    expect(screen.getByText(/Hybrid Ensemble/i)).toBeInTheDocument()
    expect(screen.getByText(/Collaborative Filtering/i)).toBeInTheDocument()
    expect(screen.getByText(/Content-Based Matching/i)).toBeInTheDocument()
    expect(screen.getByText(/NLP Sentiment Recommender/i)).toBeInTheDocument()
  })

  it('displays dataset platform statistics', () => {
    render(<Home />)
    
    expect(screen.getAllByText(/50,780/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/Indexed Properties/i)).toBeInTheDocument()
    expect(screen.getAllByText(/201,382/i).length).toBeGreaterThan(0)
  })
})
