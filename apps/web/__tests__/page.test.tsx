import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Home from '@/app/page'

describe('Home Page', () => {
  it('renders the main heading', () => {
    render(<Home />)
    
    const heading = screen.getByText(/TripSense AI/i)
    expect(heading).toBeInTheDocument()
  })

  it('displays the tagline', () => {
    render(<Home />)
    
    const tagline = screen.getByText(/Smart Hotel Recommendations/i)
    expect(tagline).toBeInTheDocument()
  })

  it('shows feature cards', () => {
    render(<Home />)
    
    // Check for feature titles
    expect(screen.getByText(/Personalized Recommendations/i)).toBeInTheDocument()
    expect(screen.getByText(/Sentiment Analysis/i)).toBeInTheDocument()
    expect(screen.getByText(/Multi-Algorithm Approach/i)).toBeInTheDocument()
  })

  it('displays the API status section', () => {
    render(<Home />)
    
    const statusSection = screen.getByText(/System Status/i)
    expect(statusSection).toBeInTheDocument()
  })
})
