import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

// Mock fetch globally
globalThis.fetch = vi.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve([]),
    ok: true,
  })
) as any;

describe('App', () => {
  it('renders the header', () => {
    render(<App />);
    expect(screen.getByText('Drone 3D Scanner')).toBeInTheDocument();
  });

  it('renders upload tab by default', () => {
    render(<App />);
    expect(screen.getByText('Start a New 3D Scan')).toBeInTheDocument();
  });

  it('switches to library tab when clicking library button', async () => {
    render(<App />);
    const libraryBtn = screen.getByText('Library');
    fireEvent.click(libraryBtn);
    expect(await screen.findByText('Scan Library')).toBeInTheDocument();
  });
});
