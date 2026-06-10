export interface Listing {
  id: string;
  source: string;
  url: string;
  title: string | null;
  year: number | null;
  make: string | null;
  model: string | null;
  generation: string | null;
  trim: string | null;
  mileage: number | null;
  price: number | null;
  title_status: string | null;
  transmission: string | null;
  listing_type: string | null;
  is_dealer: boolean;
  is_spam: boolean;
  car_category: string | null;
  photos: string[] | null;
  city: string | null;
  state: string | null;
  lat: number | null;
  lng: number | null;
  deal_rating: number | null;
  deal_confidence: string | null;
  fair_value_estimate: number | null;
  fair_value_delta: number | null;
  comp_count: number;
  red_flags: string[] | null;
  posted_at: string | null;
  scraped_at: string;
}

export interface ListingDetail extends Listing {
  raw_text: string | null;
  drivetrain: string | null;
  vin: string | null;
  modifications: string[] | null;
  deal_rationale: string | null;
  known_quirks: string[] | null;
  questions_to_ask: string[] | null;
  spam_score: number | null;
  enriched_at: string | null;
}

export interface PaginatedListings {
  total: number;
  page: number;
  per_page: number;
  pages: number;
  items: Listing[];
}

export interface MapPoint {
  id: string;
  lat: number;
  lng: number;
  score: number | null;
  make: string | null;
  model: string | null;
  year: number | null;
  price: number | null;
  title_status: string | null;
}

export interface FilterState {
  make: string;
  model: string;
  min_year: string;
  max_year: string;
  min_price: string;
  max_price: string;
  min_score: string;
  transmission: string;
  title_status: string;
  private_only: boolean;
  sort_by: string;
}
