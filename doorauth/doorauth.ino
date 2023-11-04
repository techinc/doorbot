/*
 * Copyright (c) 2013 Erik Bosman <erik@minemu.org>
 *
 * Permission  is  hereby  granted,  free  of  charge,  to  any  person
 * obtaining  a copy  of  this  software  and  associated documentation
 * files (the "Software"),  to deal in the Software without restriction,
 * including  without  limitation  the  rights  to  use,  copy,  modify,
 * merge, publish, distribute, sublicense, and/or sell copies of the
 * Software,  and to permit persons to whom the Software is furnished to
 * do so, subject to the following conditions:
 *
 * The  above  copyright  notice  and this  permission  notice  shall be
 * included  in  all  copies  or  substantial portions  of the Software.
 *
 * THE SOFTWARE  IS  PROVIDED  "AS IS", WITHOUT WARRANTY  OF ANY KIND,
 * EXPRESS OR IMPLIED,  INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY,  FITNESS  FOR  A  PARTICULAR  PURPOSE  AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM,  DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT,  TORT OR OTHERWISE,  ARISING FROM, OUT OF OR IN
 * CONNECTION  WITH THE SOFTWARE  OR THE USE  OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 * (http://opensource.org/licenses/mit-license.html)
 */

#include <avr/io.h>
#include <avr/interrupt.h>

#define KEYPAD_RX (4)
#define KEYPAD_TX (5) /* not used, but SoftwareSerial requires a pin */
#define ALARM_PIN (6)
#define LED_PIN   (7)

#define DATA0_PIN (2) /* cannot change, depends on INT0 */
#define DATA1_PIN (3) /* cannot change, depends on INT1 */

#include <SoftwareSerial.h>
SoftwareSerial keypad(KEYPAD_RX, KEYPAD_TX);

unsigned long cur;

enum
{
	OFF,
	ON,
	BLINK,

} led_mode;

/*
 * Bleeps
 */

void short_beep()
{
	digitalWrite(ALARM_PIN, LOW);
	delay(50);
	digitalWrite(ALARM_PIN, HIGH);
}

void granted_beep(void)
{
	digitalWrite(ALARM_PIN, LOW);
	delay(50);
	digitalWrite(ALARM_PIN, HIGH);
	delay(50);
	digitalWrite(ALARM_PIN, LOW);
	delay(50);
	digitalWrite(ALARM_PIN, HIGH);
	delay(50);
	digitalWrite(ALARM_PIN, LOW);
	delay(50);
	digitalWrite(ALARM_PIN, HIGH);
}

void denied_beep(void)
{
	for (int i=0; i<100; i++)
	{
		delay(4);
		digitalWrite(ALARM_PIN, LOW);
		delay(4);
		digitalWrite(ALARM_PIN, HIGH);
	}
}

/*
 * RFID reader
 */

#define BITS_MAX (256)
uint8_t rfid_code[BITS_MAX];
int rfid_code_len = 0;
volatile uint8_t rfid_read;

void rfid_clear(void)
{
	rfid_code_len = 0;
	rfid_read = 0;
	EIFR |= _BV(INTF0) | _BV(INTF1); /* clear interrupt flags */
}

void rfid_add_bit(uint8_t bit)
{
	if (!rfid_read && rfid_code_len < BITS_MAX)
		rfid_code[rfid_code_len++] = bit;
}

void rfid_print(void)
{
	int i;

	Serial.print("RFID ");
	for (i=0; i<rfid_code_len; i++)
		Serial.print((int)rfid_code[i]);

	Serial.println("");
}

int rfid_poll(void)
{
	uint8_t r;

	if ( (r = rfid_read) )
	{
		rfid_print();
		rfid_clear();
	}

	return r;
}

void reset_timer(void)
{
	TCCR1B = 0; /* stop clock */
	OCR1A = 0x1000;
	TCNT1 = 0;
	TIMSK1 = _BV(OCIE1A);
	TCCR1B = _BV(CS12); /* clock select prescaler 1/256 */
	TIFR1 |= _BV(OCF1A);
}

void stop_timer(void)
{
	OCR1A = 0x1000;
	TCCR1B = 0; /* stop clock */
	TIMSK1 = 0; /* disable interrupt */
	TCNT1 = 0;
	TIFR1 |= _BV(OCF1A);
}

ISR(TIMER1_COMPA_vect)
{
	stop_timer();
	rfid_read = 1;
}

void wiegand_read_zero(void)
{
	rfid_add_bit(0);
	reset_timer();
}

void wiegand_read_one(void)
{
	rfid_add_bit(1);
	reset_timer();
}

void rfid_init(void)
{
	rfid_clear();
	pinMode(DATA0_PIN, INPUT);
	pinMode(DATA1_PIN, INPUT);
	attachInterrupt(0, wiegand_read_zero, FALLING);
	attachInterrupt(1, wiegand_read_one, FALLING);
}

/*
 * Read PIN pad
 */

int last_key = -1;
unsigned long last_key_time;

int key_poll(void)
{
	int c = keypad.read();

	if (cur-last_key_time > 300)
		last_key = -1;

	if (c == -1)
		return 0;
 
	if ( ( (c < '0') || (c > '9') ) && (c != 'C') && (c != 'B') )
		return 0;

	if (last_key != -1)
		return 0;

	last_key_time = cur;
	last_key = c;

	Serial.print("KEY ");
	Serial.println((char)c);
}

/*
 * Control commands
 */

#define MAX_COMMAND (15)
char command[MAX_COMMAND+1];
int command_len = 0;

void command_poll()
{
	int c, i;
	while( (c = Serial.read()) != -1 )
	{
		if ( (c == '\r') || (c == '\n') || (c == '\0') )
		{
			command[command_len] = '\0';

			if ( strcmp(command, "GRANTED") == 0 )
				granted_beep();

			else if ( strcmp(command, "DENIED") == 0 )
				denied_beep();

			else if ( strcmp(command, "BEEP") == 0 )
				short_beep();

			else if ( strcmp(command, "LED ON") == 0 )
				led_mode = ON;

			else if ( strcmp(command, "LED OFF") == 0 )
				led_mode = OFF;

			else if ( strcmp(command, "LED BLINK") == 0 )
				led_mode = BLINK;

			command_len = 0;
		}
		else if (command_len < MAX_COMMAND)
			command[command_len++] = c;

	}
}

void led_update(void)
{
	if (led_mode == ON)
		digitalWrite(LED_PIN, LOW);
	else if (led_mode == BLINK)
		digitalWrite(LED_PIN, (cur & 0x200) ? HIGH : LOW );
	else
		digitalWrite(LED_PIN, HIGH);
}

void setup(void)
{
	pinMode(LED_PIN, OUTPUT);
	digitalWrite(LED_PIN, HIGH);
	digitalWrite(ALARM_PIN, HIGH);
	pinMode(ALARM_PIN, OUTPUT);
	keypad.begin(9600);
	keypad.listen();
	Serial.begin(9600);
	Serial.println("RESET");
	rfid_init();
}

void loop(void)
{
	for(;;)
	{
		cur = millis();
		rfid_poll();
		key_poll();
		command_poll();
		led_update();
	}
}

