import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright
from pathlib import Path

def get_executable_dir():
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        return os.path.dirname(sys.executable)
    else:
        # Running as a normal Python script
        return os.path.dirname(os.path.abspath(__file__))

async def book_ryanair_flight():
    # Load configuration
    config_file = Path(get_executable_dir()) / 'config.json'
    config = json.loads(config_file.read_text())

    # Extract config values
    flight_details = config['flight_details']
    passengers = config['passengers']
    booking_prefs = config['booking_preferences']
    browser_settings = config['browser_settings']

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=browser_settings['headless'],
            args=["--ignore-certificate-errors"]
        )
        page = await browser.new_page()

        # 1. Go to Ryanair website
        await page.goto('https://www.ryanair.com/')
        await page.wait_for_load_state('networkidle')
        print("Navigated to Ryanair homepage.")

        # 2. Accept privacy/cookie settings if prompted
        try:
            await page.wait_for_selector('button:has-text("Agree")', timeout=browser_settings['timeout'])
            await page.click('button:has-text("Agree")')
            print("Accepted privacy settings.")
        except Exception:
            pass  # Consent button may not appear

        # 3. Click on the departure airport input and fill in departure airport
        try:
            await page.wait_for_selector('input[id="input-button__departure"]', timeout=browser_settings['timeout'])
            await page.fill('input[id="input-button__departure"]', flight_details['departure_airport'])
            await page.wait_for_selector(f'span[data-id="{flight_details["departure_code"]}"]', timeout=browser_settings['timeout'])
            await page.click(f'span[data-id="{flight_details["departure_code"]}"]')
            print(f"Filled in departure airport as {flight_details['departure_airport']} ({flight_details['departure_code']}).")
        except Exception as e:
            print(f"Could not find or fill departure airport input: {e}")
            await browser.close()
            return

        # 4. Click on the destination airport input and fill in destination airport
        try:
            await page.fill('input[id="input-button__destination"]', flight_details['destination_airport'])
            await page.wait_for_selector(f'span[data-id="{flight_details["destination_code"]}"]', timeout=browser_settings['timeout'])
            await page.click(f'span[data-id="{flight_details["destination_code"]}"]')
            print(f"Filled in destination airport as {flight_details['destination_airport']} ({flight_details['destination_code']}).")
        except Exception as e:
            print(f"Could not find or fill destination airport input: {e}")
            await browser.close()
            return

        # 5. Select departure date
        try:
            await page.wait_for_selector('div[data-ref="input-button__dates-from"] div[data-ref="input-button__display-value"]', timeout=browser_settings['timeout'])
            await page.click('div[data-ref="input-button__dates-from"] div[data-ref="input-button__display-value"]')
            try:
                await page.wait_for_selector(f'div[data-id="{flight_details["departure_month"]}"]', timeout=browser_settings['timeout'])
                await page.click(f'div[data-id="{flight_details["departure_month"]}"]')
            except Exception:
                print(f"{flight_details['departure_month']} month not selectable.")
            await page.wait_for_selector(f'div[data-id="{flight_details["departure_date"]}"]', timeout=browser_settings['timeout'])
            await page.click(f'div[data-id="{flight_details["departure_date"]}"]')
            print(f"Selected departure date as {flight_details['departure_date']}.")
        except Exception as e:
            print(f"Could not select departure date: {e}")
            await browser.close()
            return

        # 6. Select return date
        try:
            await page.wait_for_selector(f'div[data-id="{flight_details["return_date"]}"]', timeout=browser_settings['timeout'])
            await page.click(f'div[data-id="{flight_details["return_date"]}"]')
            print(f"Selected return date as {flight_details['return_date']}.")
        except Exception as e:
            print(f"Could not select return date: {e}")
            await browser.close()
            return

        # 7. Add another adult passenger and check if 2 adults in total are selected before proceeding
        try:
            await page.wait_for_selector('[data-ref="passengers-picker__adults"]', timeout=browser_settings['timeout'])
            await page.click('[data-ref="passengers-picker__adults"] div[class="counter__button-wrapper--enabled"]')
            print("Clicked to add an adult passenger.")
        
            # Assert that the number of adults is now 2
            await page.wait_for_selector('[data-ref="passengers-picker__adults"] [data-ref="counter.counter__value"]', timeout=browser_settings['timeout'])
            adults_value = await page.inner_text('[data-ref="passengers-picker__adults"] [data-ref="counter.counter__value"]')
            adults_value = adults_value.strip()
            assert adults_value == '2', f"Expected 2 adults, but found {adults_value}"
            print("Assertion passed: 2 adults are added.")

            # Assert that the number of children is 0
            await page.wait_for_selector('[data-ref="passengers-picker__children"] [data-ref="counter.counter__value"]', timeout=browser_settings['timeout'])
            children_value = await page.inner_text('[data-ref="passengers-picker__children"] [data-ref="counter.counter__value"]')
            children_value = children_value.strip()
            assert children_value == '0', f"Expected 0 children, but found {children_value}"
            print("Assertion passed: 0 children are added.")
            await page.click('button:has-text("Done")')
        except Exception as e:
            print(f"Could not add or assert adult passenger: {e}")
            await browser.close()
            return
        
        # 8. Search for flights
        await page.click('button:has-text("Search")')
        print("Clicked on Search button to find flights.")
        await page.wait_for_load_state('networkidle')

        # 9. Select the first available outbound flight
        try:
            # Wait for the outbound flights information to load
            await page.wait_for_selector('[data-e2e="flight-card--outbound"] button:has-text("Select")', timeout=browser_settings['page_load_timeout'])
            # Click the first visible Select button in the outbound section
            select_buttons = await page.query_selector_all('[data-e2e="flight-card--outbound"] button:has-text("Select")')
            if select_buttons:
                await select_buttons[0].click()
                print("Selected the first available outbound flight.")
            else:
                raise Exception("No Select button found in outbound flights section.")
        except Exception as e:
            print(f"Could not select a flight: {e}")
            await browser.close()
            return
        
        # 10. Select the first available inbound flight
        try:
            # Wait for the inbound flights information to load
            await page.wait_for_selector('[data-e2e="flight-card--inbound"] button:has-text("Select")', timeout=browser_settings['page_load_timeout'])
            # Click the first visible Select button in the inbound section
            select_buttons = await page.query_selector_all('[data-e2e="flight-card--inbound"] button:has-text("Select")')
            if select_buttons:
                await select_buttons[0].click()
                print("Selected the first available inbound flight.")
            else:
                raise Exception("No Select button found in inbound flights section.")
        except Exception as e:
            print(f"Could not select a flight: {e}")
            await browser.close()
            return
        
        # 11. Select the fare based on config
        try:
            if booking_prefs['fare_type'] == 'basic':
                await page.wait_for_selector('[data-e2e="fare-card-standard"]', timeout=browser_settings['page_load_timeout'])
                await page.click('[data-e2e="fare-card-standard"]')
                await page.click('button:has-text("Continue with Basic")')
                print("Selected the Basic fare.")
            else:
                print(f"Fare type '{booking_prefs['fare_type']}' not implemented yet.")
        except Exception as e:
            print(f"Could not select the Basic fare.: {e}")
            await browser.close()
            return
        
        # 12. Login Later if prompted
        try:
            await page.wait_for_selector('div[class="login-touchpoint"]', timeout=browser_settings['timeout'])
            await page.click('div[class="login-touchpoint"] span:has-text("Log in later")')
            print("Chose to log in later.")
        except Exception:
            pass  # Login prompt may not appear
        
        # 13. Fill Passenger 1 adult details
        try:
            adult_passenger = passengers['adults'][0]
            # Wait for the passenger details form to appear
            await page.wait_for_selector('[data-ref="pax-details__ADT-0"] button[class="dropdown__toggle body-l-lg body-l-sm"]', timeout=browser_settings['page_load_timeout'])
            await page.click('[data-ref="pax-details__ADT-0"] button[class="dropdown__toggle body-l-lg body-l-sm"]')
            # Fill the details for Passenger 1
            await page.click(f'button:has-text("{adult_passenger["title"]}")')
            await page.fill('input[id="form.passengers.ADT-0.name"]', adult_passenger['first_name'])
            await page.fill('input[id="form.passengers.ADT-0.surname"]', adult_passenger['surname'])
            print("Filled in Passenger 1 details.")
        except Exception as e:
            print(f"Could not fill Passenger 1 details: {e}")
            await browser.close()
            return
        
        # 14. Fill Passenger 2 adult details
        try:
            adult_passenger_2 = passengers['adults'][1]
            # Wait for the passenger details form to appear
            await page.wait_for_selector('[data-ref="pax-details__ADT-1"] button[class="dropdown__toggle body-l-lg body-l-sm"]', timeout=browser_settings['page_load_timeout'])
            await page.click('[data-ref="pax-details__ADT-1"] button[class="dropdown__toggle body-l-lg body-l-sm"]')
            # Fill the details for Passenger 2
            await page.click(f'button:has-text("{adult_passenger_2["title"]}")')
            await page.fill('input[id="form.passengers.ADT-1.name"]', adult_passenger_2['first_name'])
            await page.fill('input[id="form.passengers.ADT-1.surname"]', adult_passenger_2['surname'])
            print("Filled in Passenger 2 details.")
        except Exception as e:
            print(f"Could not fill Passenger 2 details: {e}")
            await browser.close()
            return
        
        # 15. Continue to the next step
        try:
            await page.click('button:has-text("Continue")')
            print("Clicked to continue.")
        except Exception as e:
            print(f"Could not continue: {e}")
            await browser.close()
            return

        # 16. Select seats
        try:
            await page.wait_for_selector('div[class="seats-container__content"]', timeout=browser_settings['page_load_timeout'])
            await page.wait_for_load_state('networkidle')
            print("Seat selection page loaded.")
                                  
            # Assert that seats are selected for each passenger for both flights
            try:
                # Check outbound flight seats
                outbound_seats = await page.query_selector_all('td.passenger-carousel__table-cell-seat--active-column seat .seat__seat--occupied')
                outbound_seat_count = len(outbound_seats)
                print(f"Found {outbound_seat_count} selected seats for outbound flight")
                
                # Check inbound flight seats
                inbound_seats = await page.query_selector_all('td.passenger-carousel__table-cell-seat:not(.passenger-carousel__table-cell-seat--active-column) seat .seat__seat--occupied')
                inbound_seat_count = len(inbound_seats)
                print(f"Found {inbound_seat_count} selected seats for inbound flight")
                
                # Expected number of passengers (should be 2 based on config)
                expected_passengers = len(passengers['adults'])
                
                # Assert outbound flight has seats for all passengers
                assert outbound_seat_count == expected_passengers, f"Expected {expected_passengers} outbound seats, but found {outbound_seat_count}"
                print(f"Assertion passed: {expected_passengers} outbound seats are selected")
                
                # Assert inbound flight has seats for all passengers
                assert inbound_seat_count == expected_passengers, f"Expected {expected_passengers} inbound seats, but found {inbound_seat_count}"
                print(f"Assertion passed: {expected_passengers} inbound seats are selected")
                
                # Get specific seat numbers for verification
                for i in range(expected_passengers):
                    if i < len(outbound_seats):
                        outbound_seat_text = await outbound_seats[i].inner_text()
                        print(f"  Passenger {i+1} outbound seat: {outbound_seat_text}")
                    
                    if i < len(inbound_seats):
                        inbound_seat_text = await inbound_seats[i].inner_text()
                        print(f"  Passenger {i+1} inbound seat: {inbound_seat_text}")
                        
            except Exception as e:
                print(f"Seat selection assertion failed: {e}")
                await browser.close()
                return

            # Click the "Add recommended seats" button
            await page.click('button:has-text("Add recommended seats")')
            print("Selected recommended seats.")
                                   
        except Exception as e:
            print(f"Could not select seats: {e}")
            await browser.close()
            return
        
        # 17 Continue after seat selection
        try:
            await page.wait_for_selector('div[data-ref="enhanced-takeover-beta-desktop__FAST_VISUAL_TAKEOVER_2"]', timeout=browser_settings['timeout'])
            await page.click('button:has-text("No, thanks")')
        except Exception:
            pass  # Consent button may not appear

        # 18. Continue to the next step - Select small bag options
        try:               
            # Wait for small bag radio buttons to be visible
            await page.wait_for_selector('input[type="radio"][value="small-bag"]', timeout=browser_settings['page_load_timeout'])
            print("Small bag radio buttons are now visible")
            
            # Click on all radio buttons with type="radio" and value="small-bag"
            small_bag_radios = await page.query_selector_all('input[type="radio"][value="small-bag"]')
            print(f"Found {len(small_bag_radios)} small-bag radio buttons to click")
            for i, radio in enumerate(small_bag_radios):
                    # Scroll the radio button into view first
                    await radio.scroll_into_view_if_needed()
                        
                    # Click the radio button
                    await radio.click(force=True)
                    print(f"Clicked small-bag radio button {i + 1}")
                
            # Wait for selections to register
            await page.wait_for_timeout(2000)
            
            # Click continue button
            await page.wait_for_selector('button:has-text("Continue")', timeout=browser_settings['timeout'])
            await page.click('button:has-text("Continue")')
            print("Clicked to continue with bag selection.")
            
        except Exception as e:
            print(f"Could not continue with bag selection: {e}")
            await browser.close()
            return

        # 19. Pause and display for 3 seconds
        print("Finally, Pausing for 3 seconds so you can view.")
        await page.wait_for_timeout(3000)

        await browser.close()
        return


if __name__ == "__main__":
    asyncio.run(book_ryanair_flight())

