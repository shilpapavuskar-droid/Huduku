// javascript
import React, { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
const MEDIA_BASE = process.env.REACT_APP_MEDIA_BASE_URL || "http://localhost:8000";

function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [userEmail, setUserEmail] = useState("");

  const [listings, setListings] = useState([]);
  const [categoriesFlat, setCategoriesFlat] = useState([]);

  const [filters, setFilters] = useState({
    location: "",
    minPrice: "",
    maxPrice: "",
  });
  const [search, setSearch] = useState("");

  const [selectedCategoryId, setSelectedCategoryId] = useState(null);
  const [selectedSubCategoryId, setSelectedSubCategoryId] = useState(null);

  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [sellModalOpen, setSellModalOpen] = useState(false);
  const [loginSource, setLoginSource] = useState(null); // "sell" | "header" | null

  const [newListing, setNewListing] = useState({
    title: "",
    category: 1,
    subcategory: null,
    price: 0,
    location: "",
    description: "",
  });
  const [newListingImages, setNewListingImages] = useState(null); // FileList

  const isLoggedIn = Boolean(token);

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchListings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.location, filters.minPrice, filters.maxPrice, selectedCategoryId, selectedSubCategoryId]);

  const fetchListings = async () => {
    try {
      const params = new URLSearchParams();

      if (filters.location) params.append("location", filters.location);
      if (filters.minPrice) params.append("min_price", filters.minPrice);
      if (filters.maxPrice) params.append("max_price", filters.maxPrice);

      const categoryFilter = selectedSubCategoryId || selectedCategoryId;
      if (categoryFilter) params.append("category", categoryFilter);

      const url = `${API_URL}/listings-with-images${
        params.toString() ? `?${params.toString()}` : ""
      }`;

      const res = await fetch(url);
      if (!res.ok) {
        console.error("Failed to fetch listings", await res.text());
        setListings([]);
        return;
      }
      const data = await res.json();
      setListings(data);
    } catch (err) {
      console.error("Error fetching listings", err);
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await fetch(`${API_URL}/categories`);
      if (!res.ok) {
        setCategoriesFlat([
          { id: 1, name: "Electronics", parent_id: null },
          { id: 2, name: "Furniture", parent_id: null },
          { id: 11, name: "Phones", parent_id: 1 },
          { id: 12, name: "Laptops", parent_id: 1 },
          { id: 21, name: "Chairs", parent_id: 2 },
          { id: 22, name: "Tables", parent_id: 2 },
        ]);
        return;
      }
      const data = await res.json();
      setCategoriesFlat(data);
    } catch (e) {
      console.error("Error fetching categories, using placeholder.", e);
      setCategoriesFlat([
        { id: 1, name: "Electronics", parent_id: null },
        { id: 2, name: "Furniture", parent_id: null },
        { id: 11, name: "Phones", parent_id: 1 },
        { id: 12, name: "Laptops", parent_id: 1 },
        { id: 21, name: "Chairs", parent_id: 2 },
        { id: 22, name: "Tables", parent_id: 2 },
      ]);
    }
  };

  const categoriesTree = useMemo(() => {
    const roots = categoriesFlat.filter(c => c.parent_id == null);
    return roots.map(root => ({
      ...root,
      subcategories: categoriesFlat.filter(c => c.parent_id === root.id),
    }));
  }, [categoriesFlat]);

  const register = async () => {
    try {
      const res = await fetch(`${API_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        alert(
          data?.detail || data?.error || data?.message || "Registration failed"
        );
        return;
      }
      alert("Registered successfully. Please log in.");
    } catch (e) {
      console.error(e);
      alert("Network error during registration.");
    }
  };

  const login = async () => {
    try {
      const res = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok || !data.token) {
        alert(data?.detail || data?.error || data?.message || "Login failed");
        setToken("");
        return;
      }

      setToken(data.token);
      setUserEmail(email);
      setAuthModalOpen(false);

      if (loginSource === "sell") {
        setSellModalOpen(true);
      }
      setLoginSource(null);
    } catch (e) {
      console.error(e);
      setToken("");
      alert("Network error during login.");
    }
  };

  const logout = () => {
    setToken("");
    setUserEmail("");
    setAuthModalOpen(false);
    setSellModalOpen(false);
    setLoginSource(null);
    setSelectedCategoryId(null);
    setSelectedSubCategoryId(null);
  };

  const onSellClick = () => {
    if (!isLoggedIn) {
      setLoginSource("sell");
      setAuthModalOpen(true);
    } else {
      setSellModalOpen(true);
    }
  };

  const createListing = async () => {
    if (!isLoggedIn) {
      alert("Please log in first.");
      setLoginSource("sell");
      setAuthModalOpen(true);
      return;
    }

    if (!newListing.title || !newListing.location || !newListing.price) {
      alert("Please fill in title, price and location.");
      return;
    }

    if (!newListingImages || newListingImages.length === 0) {
      alert("Please upload at least one image.");
      return;
    }

    try {
      const body = {
        title: newListing.title,
        category: newListing.category,
        price: newListing.price,
        location: newListing.location,
        is_active: true,
      };

      const res = await fetch(`${API_URL}/listing/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      const data = await res.json();
      if (!res.ok) {
        alert(data?.detail || data?.error || data?.message || "Create failed");
        return;
      }

      const listingId = data.id;
      if (!listingId) {
        alert("Listing created but ID missing in response.");
        return;
      }

      for (let i = 0; i < newListingImages.length; i++) {
        const file = newListingImages[i];
        const formData = new FormData();
        formData.append("image", file);

        const imgRes = await fetch(
          `${API_URL}/listing/${listingId}/image/upload`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
            },
            body: formData,
          }
        );

        if (!imgRes.ok) {
          console.error("Image upload failed", await imgRes.text());
          alert("One of the images failed to upload.");
        }
      }

      alert("Listing created with images.");
      setSellModalOpen(false);
      setNewListing({
        title: "",
        category: 1,
        subcategory: null,
        price: 0,
        location: "",
        description: "",
      });
      setNewListingImages(null);
      fetchListings();
    } catch (e) {
      console.error(e);
      alert("Network error during listing creation.");
    }
  };

  const onCategoryClick = categoryId => {
    setSelectedCategoryId(categoryId);
    setSelectedSubCategoryId(null);
  };

  const onSubCategoryClick = (categoryId, subCategoryId) => {
    setSelectedCategoryId(categoryId);
    setSelectedSubCategoryId(subCategoryId);
  };

  const clearCategoryFilter = () => {
    setSelectedCategoryId(null);
    setSelectedSubCategoryId(null);
  };

  const applyClientFilters = item => {
    if (search) {
      const s = search.toLowerCase();
      const title = item.title?.toLowerCase() || "";
      const desc = item.description?.toLowerCase() || "";
      if (!title.includes(s) && !desc.includes(s)) return false;
    }
    return true;
  };

  const filteredListings = listings.filter(applyClientFilters);

  return (
    <div className="page-root">
      <header className="navbar">
        <div className="logo">Huduku</div>

        <nav className="category-bar">
          <button className="category-all" onClick={clearCategoryFilter}>
            All
          </button>
          {categoriesTree.map(cat => (
            <div key={cat.id} className="category-top-item">
              <button
                className={
                  "category-top-button" +
                  (selectedCategoryId === cat.id &&
                  selectedSubCategoryId == null
                    ? " active"
                    : "")
                }
                onClick={() => onCategoryClick(cat.id)}
              >
                {cat.name}
              </button>
              {cat.subcategories && cat.subcategories.length > 0 && (
                <div className="dropdown">
                  {cat.subcategories.map(sub => (
                    <button
                      key={sub.id}
                      className={
                        "dropdown-item" +
                        (selectedSubCategoryId === sub.id ? " active" : "")
                      }
                      onClick={() => onSubCategoryClick(cat.id, sub.id)}
                    >
                      {sub.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </nav>

        <div className="nav-actions">
          <button
            className="btn secondary"
            onClick={() => {
              if (!isLoggedIn) {
                setLoginSource("header");
                setAuthModalOpen(true);
              }
            }}
            disabled={isLoggedIn}
          >
            Register
          </button>

          {!isLoggedIn ? (
            <button
              className="btn secondary"
              onClick={() => {
                setLoginSource("header");
                setAuthModalOpen(true);
              }}
            >
              Login
            </button>
          ) : (
            <button className="btn secondary" onClick={logout}>
              Logout
            </button>
          )}

          <button className="btn primary" onClick={onSellClick}>
            Sell
          </button>

          <span className="status">
            {isLoggedIn ? `Logged in as ${userEmail}` : "Guest"}
          </span>
        </div>
      </header>

      <div className="layout">
        <div className="main-content">
          <section className="filter-bar">
            <div className="filter-group">
              <label className="field-inline">
                <span>Search</span>
                <input
                  type="text"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Search listings..."
                />
              </label>
              <button className="btn small" onClick={fetchListings}>
                Search
              </button>
            </div>

            <div className="filter-group">
              <label className="field-inline">
                <span>Location</span>
                <input
                  type="text"
                  value={filters.location}
                  onChange={e =>
                    setFilters({ ...filters, location: e.target.value })
                  }
                  placeholder="City, country..."
                />
              </label>
              <label className="field-inline">
                <span>Min price</span>
                <input
                  type="number"
                  value={filters.minPrice}
                  onChange={e =>
                    setFilters({ ...filters, minPrice: e.target.value })
                  }
                />
              </label>
              <label className="field-inline">
                <span>Max price</span>
                <input
                  type="number"
                  value={filters.maxPrice}
                  onChange={e =>
                    setFilters({ ...filters, maxPrice: e.target.value })
                  }
                />
              </label>
            </div>
          </section>

          <main className="listing-section">
            {filteredListings.length === 0 && (
              <div className="empty-state">No listings found.</div>
            )}
            <div className="listing-grid">
              {filteredListings.map(item => {
                const relImage


                 =
                  item.images && item.images.length > 0
                    ? item.images[0].image
                    : null;

                const firstImage = relImage ? MEDIA_BASE + relImage : null;
                return (
                  <div
                    key={item.id || `${item.title}-${item.price}`}
                    className="listing-card"
                  >
                    {firstImage && (
                      <div className="listing-image-wrapper">
                        <img
                          src={firstImage}
                          alt={item.title}
                          className="listing-image"
                        />
                      </div>
                    )}
                    <h3 className="listing-title">{item.title}</h3>
                    <p className="listing-location">{item.location}</p>
                    <p className="listing-price">${item.price}</p>
                    <p className="listing-desc">
                      {item.description || "No description provided."}
                    </p>
                  </div>
                );
              })}
            </div>
          </main>
        </div>
      </div>

      {authModalOpen && (
        <div
          className="modal-backdrop"
          onClick={() => {
            setAuthModalOpen(false);
            setLoginSource(null);
          }}
        >
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Register / Login</h2>
            <label className="field">
              <span>Email</span>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
              />
            </label>
            <label className="field">
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </label>
            <div className="button-row">
              <button
                className="btn secondary"
                onClick={register}
                disabled={isLoggedIn}
              >
                Register
              </button>
              {!isLoggedIn ? (
                <button className="btn primary" onClick={login}>
                  Login
                </button>
              ) : (
                <button className="btn primary" onClick={logout}>
                  Logout
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {sellModalOpen && (
        <div
          className="modal-backdrop"
          onClick={() => setSellModalOpen(false)}
        >
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Create Listing</h2>
            <label className="field">
              <span>Title</span>
              <input
                value={newListing.title}
                onChange={e =>
                  setNewListing({ ...newListing, title: e.target.value })
                }
              />
            </label>
            <label className="field">
              <span>Category ID</span>
              <input
                type="number"
                value={newListing.category}
                onChange={e =>
                  setNewListing({
                    ...newListing,
                    category: Number(e.target.value),
                  })
                }
              />
            </label>
            <label className="field">
              <span>Price</span>
              <input
                type="number"
                value={newListing.price}
                onChange={e =>
                  setNewListing({
                    ...newListing,
                    price: Number(e.target.value),
                  })
                }
              />
            </label>
            <label className="field">
              <span>Location</span>
              <input
                value={newListing.location}
                onChange={e =>
                  setNewListing({
                    ...newListing,
                    location: e.target.value,
                  })
                }
              />
            </label>
            <label className="field">
              <span>Description</span>
              <textarea
                value={newListing.description}
                onChange={e =>
                  setNewListing({
                    ...newListing,
                    description: e.target.value,
                  })
                }
              />
            </label>
            <label className="field">
              <span>Images \* (at least one)</span>
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={e => setNewListingImages(e.target.files)}
              />
            </label>
            <div className="button-row">
              <button
                className="btn secondary"
                onClick={() => setSellModalOpen(false)}
              >
                Cancel
              </button>
              <button className="btn primary" onClick={createListing}>
                Publish
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
