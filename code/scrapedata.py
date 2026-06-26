import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright
import time

class MayoClinicScraper:
    def __init__(self, output_dir=None):
        import os
        if output_dir is None:
            # Default to data/ directory relative to code/
            output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.base_url = "https://www.mayoclinic.org"
        self.output_dir = Path(output_dir)
        self.raw_dir = self.output_dir / "raw" / "mayo"
        self.parsed_dir = self.output_dir / "parsed" / "mayo"
        
        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.parsed_dir.mkdir(parents=True, exist_ok=True)
    
    async def get_disease_links(self, page, letter):
        """Get disease links for a specific letter"""
        url = f"{self.base_url}/diseases-conditions/index?letter={letter}"
        print(f"\n📋 Fetching diseases for letter: {letter}")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Extract all disease links from the page
            links = await page.evaluate("""
                () => {
                    const diseaseLinks = [];
                    const allLinks = document.querySelectorAll('a[href*="/diseases-conditions/"]');
                    
                    for (const link of allLinks) {
                        const href = link.href;
                        const text = link.textContent.trim();
                        
                        // Skip if it's a generic link or navigation
                        if (text.toLowerCase() === 'see' || 
                            text.length < 3 || 
                            href.includes('/index') ||
                            href.includes('#')) {
                            continue;
                        }
                        
                        // Only get links that end with disease-name pattern
                        const urlParts = href.split('/');
                        const lastPart = urlParts[urlParts.length - 1];
                        
                        if (lastPart && !lastPart.includes('index')) {
                            diseaseLinks.push({
                                title: text,
                                url: href
                            });
                        }
                    }
                    
                    // Remove duplicates
                    const seen = new Set();
                    return diseaseLinks.filter(item => {
                        if (seen.has(item.url)) return false;
                        seen.add(item.url);
                        return true;
                    });
                }
            """)
            
            print(f"   ✅ Found {len(links)} disease links")
            
            # Show first 5 as preview
            for i, link in enumerate(links[:5], 1):
                print(f"      {i}. {link['title']}")
            if len(links) > 5:
                print(f"      ... and {len(links) - 5} more")
            
            return links
            
        except Exception as e:
            print(f"   ❌ Error fetching links for {letter}: {e}")
            return []
    
    async def extract_section_content(self, page):
        """Extract content from current page"""
        data = await page.evaluate("""
            () => {
                // Function to extract content after a specific h2 heading
                const extractSectionContent = (headingText) => {
                    const items = [];
                    
                    // Find all h2 elements
                    const allH2 = Array.from(document.querySelectorAll('h2'));
                    
                    // Find the target heading (case-insensitive, partial match)
                    const targetH2 = allH2.find(h2 => {
                        const text = h2.textContent.trim().toLowerCase();
                        const search = headingText.toLowerCase();
                        return text === search || text.startsWith(search);
                    });
                    
                    if (!targetH2) return items;
                    
                    // Get all siblings after this h2 until the next h2
                    let current = targetH2.nextElementSibling;
                    
                    while (current) {
                        // Stop if we hit another h2
                        if (current.tagName === 'H2') break;
                        
                        // Skip non-content elements
                        if (current.classList && (
                            current.classList.contains('ad') || 
                            current.classList.contains('newsletter') ||
                            current.classList.contains('products')
                        )) {
                            current = current.nextElementSibling;
                            continue;
                        }
                        
                        // Extract list items first (they're usually the most structured)
                        if (current.tagName === 'UL' || current.tagName === 'OL') {
                            const listItems = current.querySelectorAll('li');
                            listItems.forEach(li => {
                                const text = li.textContent.trim();
                                if (text.length > 3 && !text.includes('[Click to view')) {
                                    items.push(text);
                                }
                            });
                        }
                        // Extract paragraphs
                        else if (current.tagName === 'P') {
                            const text = current.textContent.trim();
                            if (text.length > 15 && 
                                !text.includes('Products & Services') &&
                                !text.includes('Mayo Clinic patient') &&
                                !text.includes('straight to your inbox') &&
                                !text.includes('[Click to view') &&
                                !text.includes('We use the data')) {
                                items.push(text);
                            }
                        }
                        // Check nested divs for content
                        else if (current.tagName === 'DIV') {
                            // First get lists from divs
                            const lists = current.querySelectorAll('ul li, ol li');
                            lists.forEach(li => {
                                const text = li.textContent.trim();
                                if (text.length > 3 && !text.includes('[Click to view')) {
                                    items.push(text);
                                }
                            });
                            
                            // Then get paragraphs if no lists found
                            if (lists.length === 0) {
                                const paragraphs = current.querySelectorAll('p');
                                paragraphs.forEach(p => {
                                    const text = p.textContent.trim();
                                    if (text.length > 15 && 
                                        !text.includes('Products & Services') &&
                                        !text.includes('Mayo Clinic patient') &&
                                        !text.includes('straight to your inbox') &&
                                        !text.includes('[Click to view') &&
                                        !text.includes('We use the data')) {
                                        items.push(text);
                                    }
                                });
                            }
                        }
                        
                        current = current.nextElementSibling;
                    }
                    
                    return items;
                };
                
                // Get the title
                const h1 = document.querySelector('h1');
                const mainTitle = h1 ? h1.textContent.trim() : '';
                
                // Get overview - content after "Overview" h2
                let overview = '';
                const allH2 = Array.from(document.querySelectorAll('h2'));
                const overviewH2 = allH2.find(h2 => 
                    h2.textContent.trim().toLowerCase() === 'overview'
                );
                
                if (overviewH2) {
                    // Get paragraphs after Overview until next h2
                    let current = overviewH2.nextElementSibling;
                    const overviewParagraphs = [];
                    
                    while (current && current.tagName !== 'H2') {
                        if (current.tagName === 'P') {
                            const text = current.textContent.trim();
                            if (text.length > 20 && 
                                !text.includes('Products & Services')) {
                                overviewParagraphs.push(text);
                            }
                        }
                        current = current.nextElementSibling;
                    }
                    
                    // Use first paragraph as overview
                    if (overviewParagraphs.length > 0) {
                        overview = overviewParagraphs[0];
                    }
                }
                
                // Fallback: get first paragraph if no overview section
                if (!overview) {
                    const firstP = document.querySelector('p');
                    if (firstP) {
                        overview = firstP.textContent.trim();
                    }
                }
                
                return {
                    title: mainTitle,
                    overview: overview,
                    symptoms: extractSectionContent('Symptoms'),
                    causes: extractSectionContent('Causes'),
                    riskFactors: extractSectionContent('Risk factors'),
                    complications: extractSectionContent('Complications'),
                    prevention: extractSectionContent('Prevention'),
                    diagnosis: extractSectionContent('Diagnosis'),
                    treatment: extractSectionContent('Treatment')
                };
            }
        """)
        return data
    
    async def scrape_disease_page(self, page, disease_info, letter, index, total):
        """Scrape a single disease page including both symptoms-causes and diagnosis-treatment tabs"""
        url = disease_info['url']
        title = disease_info['title']
        
        print(f"\n   [{index}/{total}] 🔍 Scraping: {title}")
        
        try:
            base_url = url.split('?')[0].rstrip('/')
            
            # Initialize combined data structure
            combined_data = {
                'title': title,
                'overview': '',
                'symptoms': [],
                'causes': [],
                'riskFactors': [],
                'complications': [],
                'prevention': [],
                'diagnosis': [],
                'treatment': []
            }
            
            # PART 1: Scrape Symptoms & Causes page
            print(f"      📄 Tab 1/2: Symptoms & Causes")
            symptoms_url = f"{base_url}/symptoms-causes/syc-20355911"
            
            try:
                # Try to navigate to symptoms-causes page
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)
                
                # Look for symptoms-causes link on the page
                symptoms_link = await page.query_selector('a[href*="symptoms-causes"]')
                if symptoms_link:
                    symptoms_url = await symptoms_link.get_attribute('href')
                    if not symptoms_url.startswith('http'):
                        symptoms_url = f"{self.base_url}{symptoms_url}"
                    
                    await page.goto(symptoms_url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(2)
                    
                    # Wait for content
                    try:
                        await page.wait_for_selector('h2', timeout=10000)
                    except:
                        pass
                    
                    # Extract symptoms & causes data
                    symptoms_data = await self.extract_section_content(page)
                    combined_data['title'] = symptoms_data.get('title', '') or title
                    combined_data['overview'] = symptoms_data.get('overview', '')
                    combined_data['symptoms'] = symptoms_data.get('symptoms', [])
                    combined_data['causes'] = symptoms_data.get('causes', [])
                    combined_data['riskFactors'] = symptoms_data.get('riskFactors', [])
                    combined_data['complications'] = symptoms_data.get('complications', [])
                    combined_data['prevention'] = symptoms_data.get('prevention', [])
                    
                    print(f"         ✓ Symptoms: {len(combined_data['symptoms'])} items")
                    print(f"         ✓ Causes: {len(combined_data['causes'])} items")
                    print(f"         ✓ Risk Factors: {len(combined_data['riskFactors'])} items")
            except Exception as e:
                print(f"         ⚠️  Could not load symptoms-causes page: {str(e)[:50]}")
            
            # PART 2: Scrape Diagnosis & Treatment page
            print(f"      📄 Tab 2/2: Diagnosis & Treatment")
            
            try:
                # Look for diagnosis-treatment link
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)
                
                diagnosis_link = await page.query_selector('a[href*="diagnosis-treatment"]')
                if diagnosis_link:
                    diagnosis_url = await diagnosis_link.get_attribute('href')
                    if not diagnosis_url.startswith('http'):
                        diagnosis_url = f"{self.base_url}{diagnosis_url}"
                    
                    print(f"         🔗 Found diagnosis-treatment URL")
                    await page.goto(diagnosis_url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(2)
                    
                    # Wait for content
                    try:
                        await page.wait_for_selector('h2', timeout=10000)
                    except:
                        pass
                    
                    # Extract diagnosis & treatment data
                    diagnosis_data = await self.extract_section_content(page)
                    combined_data['diagnosis'] = diagnosis_data.get('diagnosis', [])
                    combined_data['treatment'] = diagnosis_data.get('treatment', [])
                    
                    print(f"         ✓ Diagnosis: {len(combined_data['diagnosis'])} items")
                    print(f"         ✓ Treatment: {len(combined_data['treatment'])} items")
                else:
                    print(f"         ⚠️  No diagnosis-treatment link found")
            except Exception as e:
                print(f"         ⚠️  Could not load diagnosis-treatment page: {str(e)[:50]}")
            
            # Save raw HTML (from last visited page)
            html_content = await page.content()
            safe_filename = re.sub(r'[^\w\s-]', '', title)[:100].strip().replace(' ', '_')
            raw_file = self.raw_dir / f"{letter}_{index:02d}_{safe_filename}.html"
            raw_file.write_text(html_content, encoding='utf-8')
            
            # Create structured JSON with all data
            structured_data = {
                "source": "Mayo Clinic",
                "url": url,
                "title": combined_data['title'],
                "overview": combined_data['overview'],
                "sections": {
                    "Symptoms": combined_data['symptoms'],
                    "Causes": combined_data['causes'],
                    "Risk Factors": combined_data['riskFactors'],
                    "Complications": combined_data['complications'],
                    "Prevention": combined_data['prevention'],
                    "Diagnosis": combined_data['diagnosis'],
                    "Treatment": combined_data['treatment']
                },
                "last_accessed": time.strftime("%Y-%m-%d")
            }
            
            # Save parsed JSON
            json_file = self.parsed_dir / f"{letter}_{index:02d}_{safe_filename}.json"
            json_file.write_text(json.dumps(structured_data, indent=2), encoding='utf-8')
            
            # Count non-empty sections
            sections_found = sum(1 for v in structured_data['sections'].values() if v)
            print(f"      ✅ Saved | Total sections found: {sections_found}/7")
            
            return structured_data
            
        except Exception as e:
            print(f"      ❌ Error: {str(e)[:100]}")
            return None
    
    async def scrape_all(self, letters=None, skip_first=0):
        """Main scraping function"""
        if letters is None:
            letters = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
        
        print(f"\n🚀 Starting Mayo Clinic Scraper (Enhanced with Diagnosis & Treatment)")
        print(f"   Letters to process: {', '.join(letters)}")
        print(f"   Will scrape ALL diseases from each letter")
        if skip_first > 0:
            print(f"   ⏭️  Skipping first {skip_first} diseases per letter")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            all_results = []
            stats = {}
            
            for letter in letters:
                print(f"\n{'='*70}")
                print(f"📖 Processing Letter: {letter}")
                print(f"{'='*70}")
                
                # Get disease links for this letter
                disease_links = await self.get_disease_links(page, letter)
                
                if not disease_links:
                    print(f"   ⚠️  No diseases found for letter {letter}")
                    stats[letter] = 0
                    continue
                
                # Skip first N diseases if requested
                if skip_first > 0:
                    if len(disease_links) <= skip_first:
                        print(f"   ⏭️  All {len(disease_links)} diseases already scraped, skipping letter {letter}")
                        stats[letter] = 0
                        continue
                    else:
                        print(f"   ⏭️  Skipping first {skip_first} diseases (already scraped)")
                        disease_links = disease_links[skip_first:]
                        print(f"   📋 Remaining: {len(disease_links)} diseases to scrape")
                
                # Scrape each disease page
                success_count = 0
                total_diseases = len(disease_links)
                for i, disease_info in enumerate(disease_links, 1):
                    result = await self.scrape_disease_page(page, disease_info, letter, i, total_diseases)
                    if result:
                        all_results.append(result)
                        success_count += 1
                    
                    # Small delay between requests to be respectful
                    await asyncio.sleep(1)
                
                stats[letter] = success_count
                print(f"\n   ✅ Letter {letter} complete: {success_count}/{total_diseases} diseases scraped successfully")
            
            await browser.close()
            
            # Save summary
            summary = {
                "total_diseases_scraped": len(all_results),
                "letters_processed": letters,
                "diseases_per_letter": stats,
                "scrape_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "output_directories": {
                    "raw_html": str(self.raw_dir),
                    "parsed_json": str(self.parsed_dir)
                },
                "features": ["symptoms", "causes", "risk_factors", "complications", "prevention", "diagnosis", "treatment"]
            }
            
            summary_file = self.output_dir / "mayo_scrape_summary.json"
            summary_file.write_text(json.dumps(summary, indent=2), encoding='utf-8')
            
            print(f"\n{'='*70}")
            print(f"🎉 SCRAPING COMPLETE!")
            print(f"{'='*70}")
            print(f"   Total diseases scraped: {len(all_results)}")
            print(f"   Letters processed: {len(letters)}")
            print(f"\n📁 Output locations:")
            print(f"   Raw HTML: {self.raw_dir}")
            print(f"   Parsed JSON: {self.parsed_dir}")
            print(f"   Summary: {summary_file}")
            print(f"{'='*70}\n")
            
            return all_results


async def main():
    scraper = MayoClinicScraper()
    
    # Test with just letter 'A' first
    print("🧪 Testing with letter 'A'...")
    await scraper.scrape_all(letters=['A'])
    
    # Once verified, uncomment to scrape all letters:
    # await scraper.scrape_all()  # All A-Z
    
    # Or scrape specific letters:
    # await scraper.scrape_all(letters=['A', 'B', 'C'])

if __name__ == "__main__":
    asyncio.run(main())