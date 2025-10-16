def list():
    print('''
index.html
<frameset cols="50%,50%">
  <frame src="frame1.html">
  <frame src="frame2.html">
</frameset>

frame1.html
<!DOCTYPE html>
<html>
<body>
  <a href="https://google.com">Visit Google</a>
  <ul>
    <li>HTML</li>
    <li>CSS</li>
    <li>JS</li>
  </ul>
</body>
</html>


frame2.html
<!DOCTYPE html>
<html>
<body>
  <img src="image.jpg" alt="Sample Image"><br><br>
  <table border="1">
    <tr><th>Name</th><th>Age</th></tr>
    <tr><td>Ali</td><td>21</td></tr>
  </table><br><br>
  <form>
    Name: <input type="text"><br>
    Email: <input type="email"><br>
    <input type="submit">
  </form>
</body>
</html>
''')

def hotspot():
    print('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>India Map Hotspot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background: #f9f9f9;
        }
        h1 {
            color: #333;
        }
        .c {
            position: relative;
            display: inline-block;
        }
        img {
            width: 595px;
            height: 690px;
        }
        .hs {
            position: absolute;
            width: 20px;
            height: 20px;
            background: red;
            border-radius: 50%;
            cursor: pointer;
        }
        .ker { top: 600px; left: 160px; }
        .tn { top: 575px; left: 200px; }
        .ka { top: 490px; left: 160px; }
        .de { top: 200px; left: 180px; }
        .ma { top: 400px; left: 170px; }
        #ib {
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #fff;
            padding: 20px;
            border: 1px solid #ccc;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            z-index: 10;
        }
        #ib h2 {
            margin: 0;
            color: #444;
        }
        #ib p {
            color: #555;
        }
        #ib button {
            margin-top: 10px;
            padding: 5px 10px;
            background: #007BFF;
            color: #fff;
            border: none;
            cursor: pointer;
        }
        #ib button:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <h1>Interactive India Map with Hotspots</h1>
    <div class="c">
        <img src="india.jpeg" alt="India Map">
        <div class="hs ker" onclick="sl('Kerala', 'Capital: Thiruvananthapuram<br>Population: 33.4M<br>Language: Malayalam')"></div>
        <div class="hs tn" onclick="sl('Tamil Nadu', 'Capital: Chennai<br>Population: 72.1M<br>Language: Tamil')"></div>
        <div class="hs ka" onclick="sl('Karnataka', 'Capital: Bengaluru<br>Population: 61.1M<br>Language: Kannada')"></div>
        <div class="hs de" onclick="sl('Delhi', 'Capital: New Delhi<br>Population: 16.8M<br>Language: Hindi, English')"></div>
        <div class="hs ma" onclick="sl('Maharashtra', 'Capital: Mumbai<br>Population: 112.4M<br>Language: Marathi')"></div>
    </div>
    <div id="ib">
        <h2 id="sn"></h2>
        <p id="si"></p>
        <button onclick="cl()">Close</button>
    </div>
    <script>
        function sl(s, i) {
            document.getElementById('sn').innerHTML = s;
            document.getElementById('si').innerHTML = i;
            document.getElementById('ib').style.display = 'block';
        }
        function cl() {
            document.getElementById('ib').style.display = 'none';
        }
    </script>
</body>
</html>
''')

def css():
    print('''
index.html
<!DOCTYPE html>
<html>
<head>
  <title>CSS Types</title>
  <style>
    body { background-color: lightblue; }
    h1 { color: green; }
  </style>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <h1 style="color: red;">This uses inline CSS</h1>
  <p>This uses internal CSS</p>
  <div class="external">This uses external CSS</div>
</body>
</html>

style.css
.external {
  color: blue;
  font-weight: bold;
}
''')

def calc():
    print('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Calculator</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background-color: #f4f4f4;
        }
        .calculator {
            width: 300px;
            margin: 50px auto;
            padding: 20px;
            background: white;
            box-shadow: 0px 0px 10px gray;
            border-radius: 10px;
        }
        input, select, button {
            width: 100%;
            margin: 10px 0;
            padding: 10px;
            font-size: 18px;
        }
        button {
            background: blue;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background: darkblue;
        }
    </style>
</head>
<body>
    <h1>Simple Calculator</h1>
    <div class="calculator">
        <input type="number" id="num1" placeholder="Enter first number">
        <select id="operation">
            <option value="add">Addition (+)</option>
            <option value="subtract">Subtraction (-)</option>
            <option value="multiply">Multiplication (×)</option>
            <option value="divide">Division (÷)</option>
        </select>
        <input type="number" id="num2" placeholder="Enter second number"> 
        <button onclick="calculate()">Calculate</button>
        <h2>Result: <span id="result">0</span></h2>
    </div>
    <script>
        function calculate() {
            let num1 = parseFloat(document.getElementById("num1").value);
            let num2 = parseFloat(document.getElementById("num2").value);
            let operation = document.getElementById("operation").value;
            let result;
            if (isNaN(num1) || isNaN(num2)) {
                result = "Please enter valid numbers!";
            } else {
                switch (operation) {
                    case "add":
                        result = num1 + num2;
                        break;
                    case "subtract":
                        result = num1 - num2;
                        break;
                    case "multiply":
                        result = num1 * num2;
                        break;
                    case "divide":
                        result = num2 !== 0 ? num1 / num2 : "Cannot divide by zero!";
                        break;
                    default:
                        result = "Invalid operation";
                }
            }
            document.getElementById("result").textContent = result;
        }
    </script>
</body>
</html>
''')

def form():
    print('''
<!DOCTYPE html>
<html>
<head>
  <title>Login and Registration Form</title>
</head>
<body>

  <h2>Login Form</h2>
  <form id="loginForm">
    <input type="email" id="loginEmail" placeholder="Email">
    <input type="password" id="loginPassword" placeholder="Password">
    <button type="submit">Login</button>
    <div id="loginError" class="error"></div>
  </form>

  <h2>Registration Form</h2>
  <form id="registerForm">
    <input type="text" id="registerName" placeholder="Full Name">
    <input type="email" id="registerEmail" placeholder="Email">
    <input type="password" id="registerPassword" placeholder="Password">
    <input type="password" id="confirmPassword" placeholder="Confirm Password">
    <button type="submit">Register</button>
    <div id="registerError" class="error"></div>
  </form>

  <script>
    // Login validation
    document.getElementById('loginForm').addEventListener('submit', function(e) {
      e.preventDefault();
      const email = document.getElementById('loginEmail').value;
      const password = document.getElementById('loginPassword').value;
      const errorDiv = document.getElementById('loginError');

      if (!email || !password) {
        errorDiv.textContent = "All fields are required.";
        return;
      }
      if (!validateEmail(email)) {
        errorDiv.textContent = "Invalid email format.";
        return;
      }
      errorDiv.textContent = "Login successful!";
    });

    // Registration validation
    document.getElementById('registerForm').addEventListener('submit', function(e) {
      e.preventDefault();
      const name = document.getElementById('registerName').value;
      const email = document.getElementById('registerEmail').value;
      const password = document.getElementById('registerPassword').value;
      const confirm = document.getElementById('confirmPassword').value;
      const errorDiv = document.getElementById('registerError');

      if (!name || !email || !password || !confirm) {
        errorDiv.textContent = "All fields are required.";
        return;
      }
      if (!validateEmail(email)) {
        errorDiv.textContent = "Invalid email format.";
        return;
      }
      if (password.length < 6) {
        errorDiv.textContent = "Password must be at least 6 characters.";
        return;
      }
      if (password !== confirm) {
        errorDiv.textContent = "Passwords do not match.";
        return;
      }
      errorDiv.textContent = "Registration successful!";
    });

    function validateEmail(email) {
      const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return re.test(email.toLowerCase());
    }
  </script>

</body>
</html>
''')

def event():
    print('''
<!DOCTYPE html>
<html>
<head>
  <title>jQuery Events Example</title>
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
  <style>
    #box { width: 200px; height: 100px; background-color: lightblue; margin-bottom: 10px; }
    input { padding: 8px; }
  </style>
</head>
<body>

  <div id="box">Hover or Click Me</div>
  <button id="myBtn">Click Me</button><br><br>
  <input type="text" id="myInput" placeholder="Type something...">
  <p id="output"></p>

  <script>
    // Click event
    $('#myBtn').click(function() {
      alert('Button clicked!');
    });

    // Mouse enter and leave events
    $('#box').mouseenter(function() {
      $(this).css('background-color', 'lightgreen');
    }).mouseleave(function() {
      $(this).css('background-color', 'lightblue');
    });

    // Keyup event
    $('#myInput').keyup(function() {
      $('#output').text('You typed: ' + $(this).val());
    });
  </script>

</body>
</html>

''')

def effect():
    print('''
<!DOCTYPE html>
<html>
<head>
  <title>jQuery Effects Demo</title>
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
  <style>
    #box {
      width: 200px;
      height: 100px;
      background-color: coral;
      display: none;
      margin-bottom: 20px;
    }
    button {
      margin: 5px;
    }
  </style>
</head>
<body>

  <div id="box"></div>

  <button id="showBtn">Show</button>
  <button id="hideBtn">Hide</button>
  <button id="fadeBtn">Fade Toggle</button>
  <button id="slideBtn">Slide Toggle</button>
  <button id="animateBtn">Animate</button>

  <script>
    $('#showBtn').click(function() {
      $('#box').show(500); // 500ms
    });

    $('#hideBtn').click(function() {
      $('#box').hide(500);
    });

    $('#fadeBtn').click(function() {
      $('#box').fadeToggle(500);
    });

    $('#slideBtn').click(function() {
      $('#box').slideToggle(500);
    });

    $('#animateBtn').click(function() {
      $('#box').animate({
        width: '300px',
        height: '150px',
        opacity: 0.5
      }, 1000); // 1 second
    });
  </script>

</body>
</html>

''')

def grid():
    print('''
<!DOCTYPE html>
<html>
<head>
  <title>Bootstrap Grid & Buttons</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- Bootstrap 5 CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>

<div class="container mt-5">
  <h2 class="text-center mb-4">Bootstrap Grid & Buttons Demo</h2>

  <div class="row mb-4">
    <div class="col-md-4 text-center">
      <button class="btn btn-primary btn-lg">Primary</button>
    </div>
    <div class="col-md-4 text-center">
      <button class="btn btn-success">Success</button>
    </div>
    <div class="col-md-4 text-center">
      <button class="btn btn-outline-danger btn-sm">Danger (Outline)</button>
    </div>
  </div>

  <div class="row">
    <div class="col-sm-6 col-lg-3 bg-light p-3 border text-center">Grid Col 1</div>
    <div class="col-sm-6 col-lg-3 bg-warning p-3 border text-center">Grid Col 2</div>
    <div class="col-sm-6 col-lg-3 bg-info p-3 border text-center">Grid Col 3</div>
    <div class="col-sm-6 col-lg-3 bg-success text-white p-3 border text-center">Grid Col 4</div>
  </div>
</div>

<!-- Bootstrap JS (optional) -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
''')

def panel():
    print('''
<!DOCTYPE html>
<html>
<head>
  <title>Bootstrap Panels & Pagination</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- Bootstrap 5 CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>

<div class="container mt-5">

  <h2 class="text-center mb-4">Bootstrap Panels (Cards) & Pagination</h2>

  <!-- Panels Section -->
  <div class="row g-4">
    <div class="col-md-4">
      <div class="card">
        <div class="card-header bg-primary text-white">Panel 1</div>
        <div class="card-body">
          <p class="card-text">This is some content inside Panel 1.</p>
          <a href="#" class="btn btn-sm btn-outline-primary">Read More</a>
        </div>
      </div>
    </div>

    <div class="col-md-4">
      <div class="card">
        <div class="card-header bg-success text-white">Panel 2</div>
        <div class="card-body">
          <p class="card-text">This is some content inside Panel 2.</p>
          <a href="#" class="btn btn-sm btn-outline-success">Read More</a>
        </div>
      </div>
    </div>

    <div class="col-md-4">
      <div class="card">
        <div class="card-header bg-warning text-dark">Panel 3</div>
        <div class="card-body">
          <p class="card-text">This is some content inside Panel 3.</p>
          <a href="#" class="btn btn-sm btn-outline-warning">Read More</a>
        </div>
      </div>
    </div>
  </div>

  <!-- Pagination Section -->
  <nav aria-label="Page navigation example" class="mt-5">
    <ul class="pagination justify-content-center">
      <li class="page-item disabled">
        <a class="page-link">Previous</a>
      </li>
      <li class="page-item"><a class="page-link" href="#">1</a></li>
      <li class="page-item active" aria-current="page">
        <a class="page-link" href="#">2</a>
      </li>
      <li class="page-item"><a class="page-link" href="#">3</a></li>
      <li class="page-item">
        <a class="page-link" href="#">Next</a>
      </li>
    </ul>
  </nav>

</div>

<!-- Bootstrap JS (optional) -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
''')
    
def time():
 print('''
<%@ page import="java.util.Date, java.text.SimpleDateFormat" %>
<!DOCTYPE html>
<html>
<head>
    <title>Current Date and Time</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin-top: 50px;
        }
        .container {
            padding: 20px;
            border: 2px solid #333;
            display: inline-block;
            background-color: #f9f9f9;
        }
        h2 {
            color: #007bff;
        }
        p {
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Current Date and Time</h2>
        <%
            Date now = new Date();
            SimpleDateFormat dateFormat = new SimpleDateFormat("EEEE, dd MMMM yyyy");
            SimpleDateFormat timeFormat = new SimpleDateFormat("hh:mm:ss a");
        %>
        <p><b>Date:</b> <%= dateFormat.format(now) %></p>
        <p><b>Time:</b> <%= timeFormat.format(now) %></p>
    </div>
</body>
</html>
''')
 
def food():
    print('''
<?xml version="1.0" encoding="UTF-8"?>
<menu>
  <category name="Starters">
    <item>
      <name>Spring Rolls</name>
      <description>Crispy rolls stuffed with vegetables and served with dipping sauce.</description>
      <price>4.99</price>
    </item>
    <item>
      <name>Bruschetta</name>
      <description>Toasted bread with tomatoes, basil, and garlic.</description>
      <price>5.49</price>
    </item>
  </category>
  
  <category name="Main Course">
    <item>
      <name>Grilled Chicken</name>
      <description>Marinated chicken grilled to perfection, served with sides.</description>
      <price>12.99</price>
    </item>
    <item>
      <name>Veggie Burger</name>
      <description>A delicious plant-based burger served with fries.</description>
      <price>10.99</price>
    </item>
  </category>

  <category name="Desserts">
    <item>
      <name>Chocolate Cake</name>
      <description>Rich chocolate cake topped with ganache.</description>
      <price>6.49</price>
    </item>
    <item>
      <name>Apple Pie</name>
      <description>Classic apple pie served with vanilla ice cream.</description>
      <price>5.99</price>
    </item>
  </category>

  <category name="Drinks">
    <item>
      <name>Coffee</name>
      <description>Freshly brewed hot coffee.</description>
      <price>2.99</price>
    </item>
    <item>
      <name>Soft Drink</name>
      <description>Choose from a variety of sodas.</description>
      <price>1.99</price>
    </item>
  </category>
</menu>
''')

def cd():
    print('''
cd_catalogue.xml
<?xml version="1.0" encoding="UTF-8"?>
<catalogue>
  <cd>
    <title>Abbey Road</title>
    <artist>The Beatles</artist>
    <country>UK</country>
    <company>Apple Records</company>
    <price>19.99</price>
    <year>1969</year>
  </cd>
  <cd>
    <title>Dark Side of the Moon</title>
    <artist>Pink Floyd</artist>
    <country>UK</country>
    <company>Harvest Records</company>
    <price>18.99</price>
    <year>1973</year>
  </cd>
  <cd>
    <title>Back in Black</title>
    <artist>AC/DC</artist>
    <country>Australia</country>
    <company>Columbia</company>
    <price>14.99</price>
    <year>1980</year>
  </cd>
</catalogue>

styles.css
/* Style for the CD catalogue */
body {
  font-family: Arial, sans-serif;
  margin: 20px;
  background-color: #f4f4f9;
}

h1 {
  text-align: center;
  color: #333;
}

.catalogue {
  width: 80%;
  margin: 0 auto;
  border-collapse: collapse;
}

.catalogue th, .catalogue td {
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.catalogue th {
  background-color: #4CAF50;
  color: white;
}

.catalogue tr:nth-child(even) {
  background-color: #f2f2f2;
}

.catalogue tr:hover {
  background-color: #ddd;
}

transform.xsl
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  
  <!-- Output HTML -->
  <xsl:output method="html" encoding="UTF-8" />

  <!-- Template for matching the root element -->
  <xsl:template match="/catalogue">
    <html>
      <head>
        <title>CD Catalogue</title>
        <link rel="stylesheet" type="text/css" href="styles.css" />
      </head>
      <body>
        <h1>CD Catalogue</h1>
        <table class="catalogue">
          <thead>
            <tr>
              <th>Title</th>
              <th>Artist</th>
              <th>Country</th>
              <th>Company</th>
              <th>Price</th>
              <th>Year</th>
            </tr>
          </thead>
          <tbody>
            <xsl:apply-templates select="cd" />
          </tbody>
        </table>
      </body>
    </html>
  </xsl:template>

  <!-- Template for matching each CD element -->
  <xsl:template match="cd">
    <tr>
      <td><xsl:value-of select="title" /></td>
      <td><xsl:value-of select="artist" /></td>
      <td><xsl:value-of select="country" /></td>
      <td><xsl:value-of select="company" /></td>
      <td><xsl:value-of select="price" /></td>
      <td><xsl:value-of select="year" /></td>
    </tr>
  </xsl:template>

</xsl:stylesheet>

''')

def session():
    print('''
SessionServlet.java

import java.io.IOException;
import java.io.PrintWriter;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
@WebServlet("/session")  // Maps to /session
public class SessionServlet extends HttpServlet {
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        response.setContentType("text/html");
        PrintWriter out = response.getWriter();
        String username = request.getParameter("username");
        HttpSession session = request.getSession();
        session.setAttribute("user", username);
        String sessionId = session.getId();
out.println("<!DOCTYPE html>");
out.println("<html lang='en'>");
out.println("<head>");
out.println("<meta charset='UTF-8'>");
out.println("<meta name='viewport' content='width=device-width, initial-scale=1.0'>");
out.println("<title>Welcome</title>");
out.println("<style>");
out.println("body { font-family: Arial, sans-serif; text-align: center; background-color: #f4f4f4; padding: 50px; }");
out.println(".container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); max-width: 400px; margin: auto; }");
out.println("h2 { color: #333; }");
out.println("a { display: inline-block; text-decoration: none; background: #28a745; color: white; padding: 10px 20px; border-radius: 5px; margin-top: 10px; }");
out.println("a:hover { background: #218838; }");
out.println("</style>");
out.println("</head>");
out.println("<body>");
out.println("<div class='container'>");
out.println("<h2>Welcome, " + username + "!</h2>");
out.println("<p>Session ID: <strong>" + sessionId + "</strong></p>");
out.println("<a href='dashboard'>Go to Dashboard</a>");
out.println("</div>");
out.println("</body>");
out.println("</html>");
    }
}

DashboardServlet.java

import java.io.IOException;
import java.io.PrintWriter;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
@WebServlet("/dashboard")  // Maps to /dashboard
public class DashboardServlet extends HttpServlet {
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        response.setContentType("text/html");
        PrintWriter out = response.getWriter();
        HttpSession session = request.getSession(false);
        if (session != null && session.getAttribute("user") != null) {
    String username = (String) session.getAttribute("user");
    String sessionId = session.getId(); 
    out.println("<!DOCTYPE html>");
    out.println("<html lang='en'>");
    out.println("<head>");
    out.println("<meta charset='UTF-8'>");
    out.println("<meta name='viewport' content='width=device-width, initial-scale=1.0'>");
    out.println("<title>Dashboard</title>");
    out.println("<style>");
    out.println("body { font-family: Arial, sans-serif; text-align: center; background-color: #f8f9fa; padding: 50px; }");
    out.println(".container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); max-width: 400px; margin: auto; }");
    out.println("h2 { color: #007bff; }");
    out.println(".btn { display: inline-block; text-decoration: none; background: #dc3545; color: white; padding: 10px 20px; border-radius: 5px; margin-top: 10px; font-weight: bold; }");
    out.println(".btn:hover { background: #c82333; }");
    out.println("</style>");
    out.println("</head>");
    out.println("<body>");
    out.println("<div class='container'>");
    out.println("<h2>Welcome to Your Dashboard, " + username + "!</h2>");
    out.println("<p>Session ID: <strong>" + sessionId + "</strong></p>");
    out.println("<p>Manage your session and explore the features.</p>");
    out.println("<a href='logout' class='btn'>Logout</a>");
    out.println("</div>");
    out.println("</body>");
    out.println("</html>");
} else {
    out.println("<!DOCTYPE html>");
    out.println("<html lang='en'>");
    out.println("<head>");
    out.println("<meta charset='UTF-8'>");
    out.println("<meta name='viewport' content='width=device-width, initial-scale=1.0'>");
    out.println("<title>Session Expired</title>");
    out.println("<style>");
    out.println("body { font-family: Arial, sans-serif; text-align: center; background-color: #f8d7da; padding: 50px; }");
    out.println(".container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); max-width: 400px; margin: auto; }");
    out.println("h2 { color: #721c24; }");
    out.println(".btn { display: inline-block; text-decoration: none; background: #007bff; color: white; padding: 10px 20px; border-radius: 5px; margin-top: 10px; font-weight: bold; }");
    out.println(".btn:hover { background: #0056b3; }");
    out.println("</style>");
    out.println("</head>");
    out.println("<body>");
    out.println("<div class='container'>");
    out.println("<h2>Session Expired</h2>");
    out.println("<p>Your session is no longer active. Please log in again.</p>");
    out.println("<a href='index.html' class='btn'>Login Again</a>");
    out.println("</div>");
    out.println("</body>");
    out.println("</html>");
        }
    }
}

LogoutServlet.java

import java.io.IOException;
import java.io.PrintWriter;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
@WebServlet("/logout")  // Maps to /logout
public class LogoutServlet extends HttpServlet {
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
            throws ServletException, IOException {
        response.setContentType("text/html");
        PrintWriter out = response.getWriter();
        HttpSession session = request.getSession(false);
        String sessionId = (session != null) ? session.getId() : "No session found";
        if (session != null) {
            session.invalidate();
        }
        out.println("<!DOCTYPE html>");
out.println("<html lang='en'>");
out.println("<head>");
out.println("<meta charset='UTF-8'>");
out.println("<meta name='viewport' content='width=device-width, initial-scale=1.0'>");
out.println("<title>Logout Successful</title>");
out.println("<p>Session ID before logout: <strong>" + sessionId + "</strong></p>");
out.println("<style>");
out.println("body { font-family: Arial, sans-serif; text-align: center; background-color: #f8f9fa; padding: 50px; }");
out.println(".container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); max-width: 400px; margin: auto; }");
out.println("h2 { color: #28a745; }");
out.println("p { color: #555; font-size: 16px; }");
out.println(".btn { display: inline-block; text-decoration: none; background: #007bff; color: white; padding: 10px 20px; border-radius: 5px; margin-top: 10px; font-weight: bold; transition: 0.3s; }");
out.println(".btn:hover { background: #0056b3; }");
out.println("</style>");
out.println("</head>");
out.println("<body>");
out.println("<div class='container'>");
out.println("<h2>Logout Successful</h2>");
out.println("<p>You have been logged out safely. Thank you for visiting!</p>");
out.println("<a href='index.html' class='btn'>Login Again</a>");
out.println("</div>");
out.println("</body>");
out.println("</html>");
    }
}

index.html 

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login Page</title>
</head>
<body>
    <div class="container">
        <h2>Login</h2>
        <form action="session" method="post">
            <input type="text" name="username" placeholder="Enter your name" required>
            <button type="submit" class="btn">Login</button>
        </form>
    </div>
</body>
</html>
''')

def webapp():
    print('''
index.html

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AJAX Web App</title>
  
    <script>
        function fetchData() {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "DataServlet", true);
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4 && xhr.status === 200) document.getElementById("result").innerHTML = xhr.responseText;
            };
            xhr.send();
        }
    </script>
</head>
<body>
    <div class="container">
        <h2>AJAX Web Application</h2>
        <button onclick="fetchData()">Fetch Data</button>
        <div id="result"></div>
    </div>
</body>
</html>


DataServlet.java

import java.io.IOException;
import java.io.PrintWriter;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.util.Date;

@WebServlet("/DataServlet")
public class DataServlet extends HttpServlet {
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        response.setContentType("text/plain");
        PrintWriter out = response.getWriter();
        out.println("Current Server Time: " + new Date());
    }
}

''')

def form2():
    print('''
<!DOCTYPE html>
<html>
<head>
  <title>Registration Form</title>
  <style>
    body {
      font-family: Arial;
      padding: 20px;
    }
    input, select, textarea {
      display: block;
      margin-bottom: 10px;
      padding: 8px;
      width: 300px;
    }
    label {
      font-weight: bold;
    }
  </style>
</head>
<body>
  <h2>Registration Form</h2>
  <form id="regForm" onsubmit="return validateForm()">
    <label>Full Name:</label>
    <input type="text" id="fullname" />

    <label>Username:</label>
    <input type="text" id="username" />

    <label>Email:</label>
    <input type="text" id="email" />

    <label>State:</label>
    <select id="state">
      <option value="">--Select State--</option>
      <option value="CA">California</option>
      <option value="NY">New York</option>
      <option value="TX">Texas</option>
    </select>

    <label>Address:</label>
    <textarea id="address"></textarea>

    <label>Zip Code:</label>
    <input type="text" id="zipcode" />

    <label>Contact Number:</label>
    <input type="text" id="contact" />

    <label>Message:</label>
    <input type="text" id="message" />

    <button type="submit">Register</button>
  </form>

  <script>
    function validateForm() {
      let fullname = document.getElementById("fullname").value.trim();
      let username = document.getElementById("username").value.trim();
      let email = document.getElementById("email").value.trim();
      let state = document.getElementById("state").value;
      let address = document.getElementById("address").value.trim();
      let zipcode = document.getElementById("zipcode").value.trim();
      let contact = document.getElementById("contact").value.trim();
      let message = document.getElementById("message").value.trim();

      // i) Empty Field Check
      if (!fullname || !username || !email || !state || !address || !zipcode || !contact || !message) {
        alert("All fields are required.");
        return false;
      }

      // ii) Check for Numbers in Contact
      if (!/^\d+$/.test(contact)) {
        alert("Contact field should contain only numbers.");
        return false;
      }

      // iii) Check for Alphabets in Full Name
      if (!/^[A-Za-z\s]+$/.test(fullname)) {
        alert("Full Name should contain only alphabets.");
        return false;
      }

      // iv) Alphanumeric Check for Message
      if (!/^[A-Za-z0-9\s]+$/.test(message)) {
        alert("Message should contain only letters and numbers.");
        return false;
      }

      // v) Username length (example: between 4 to 12 characters)
      if (username.length < 4 || username.length > 12) {
        alert("Username must be between 4 and 12 characters long.");
        return false;
      }

      // vi) State Dropdown Check
      if (state === "") {
        alert("Please select a state.");
        return false;
      }

      // vii) Email Validation
      let emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailPattern.test(email)) {
        alert("Please enter a valid email address.");
        return false;
      }

      alert("Form submitted successfully!");
      return true;
    }
  </script>
</body>
</html>
''')

def fact():
    print('''
<!DOCTYPE html>
<html>
<head>
  <title>Number Operations</title>
  <style>
    body {
      font-family: Arial;
      padding: 20px;
    }
    input, button {
      padding: 8px;
      margin-bottom: 10px;
    }
    #result {
      margin-top: 20px;
      font-size: 16px;
    }
  </style>
</head>
<body>

  <h2>Enter a Number</h2>
  <input type="number" id="numberInput" placeholder="Enter a number" />
  <br />
  <button onclick="calculate()">Submit</button>

  <div id="result"></div>

  <script>
    function calculate() {
      let N = parseInt(document.getElementById("numberInput").value);
      let resultDiv = document.getElementById("result");

      if (isNaN(N) || N < 0) {
        resultDiv.innerHTML = "<p>Please enter a valid non-negative number.</p>";
        return;
      }

      // i) Factorial
      let factorial = 1;
      for (let i = 1; i <= N; i++) {
        factorial *= i;
      }

      // ii) Fibonacci series
      let fib = [];
      let a = 0, b = 1;
      for (let i = 0; i < N; i++) {
        fib.push(a);
        [a, b] = [b, a + b];
      }

      // iii) Multiplication table
      let table = "";
      for (let i = 1; i <= 10; i++) {
        table += `${N} × ${i} = ${N * i}<br>`;
      }

      // Display result
      resultDiv.innerHTML = `
        <p><strong>Factorial of ${N}:</strong> ${factorial}</p>
        <p><strong>Fibonacci series (${N} terms):</strong> ${fib.join(', ')}</p>
        <p><strong>Multiplication Table of ${N}:</strong><br>${table}</p>
      `;
    }
  </script>

</body>
</html>
    ''')

def formimg():
    print('''
<!DOCTYPE html>
<html>
<head>
  <title>Registration Form</title>
  <style>
    label {
      display: inline-block;
      width: 150px;
      margin-bottom: 10px;
    }
    input[type="text"], input[type="email"], input[type="password"], select {
      width: 200px;
    }
    .required {
      color: red;
    }
    .buttons {
      margin-top: 10px;
    }
  </style>
</head>
<body>

  <h3>17. Write the HTML code to display the form.</h3>

  <form>
    <label>Name <span class="required">*</span></label>
    <input type="text" name="name" required><br>

    <label>Address</label>
    <input type="text" name="address"><br>

    <label>Zip Code <span class="required">*</span></label>
    <input type="text" name="zipcode" required><br>

    <label>Country <span class="required">*</span></label>
    <select name="country" required>
      <option value="">Please select...</option>
      <option value="India">India</option>
      <option value="USA">USA</option>
      <option value="UK">UK</option>
    </select><br>

    <label>Gender <span class="required">*</span></label>
    <input type="radio" name="gender" value="Male" required> Male
    <input type="radio" name="gender" value="Female"> Female<br>

    <label>Preferences <span class="required">*</span></label>
    <input type="checkbox" name="preference" value="Red"> Red
    <input type="checkbox" name="preference" value="Green"> Green
    <input type="checkbox" name="preference" value="Blue"> Blue<br>

    <label>Phone <span class="required">*</span></label>
    <input type="text" name="phone" required><br>

    <label>Email</label>
    <input type="email" name="email"><br>

    <label>Password (6–8 characters) <span class="required">*</span></label>
    <input type="password" name="password" minlength="6" maxlength="8" required><br>

    <label>Verify Password <span class="required">*</span></label>
    <input type="password" name="verify_password" required><br>

    <div class="buttons">
      <input type="submit" value="SEND">
      <input type="reset" value="CLEAR">
    </div>
  </form>

</body>
</html>
''')
    
def welcome():
    print('''
<!DOCTYPE html>
<html>
<head>
  <title>Welcome Message</title>
  <script>
    function showWelcomeMessage() {
      alert("Welcome! Thank you for visiting our site.");
    }
  </script>
</head>
<body>

  <h2>Click the Button</h2>

  <form>
    <button type="button" onclick="showWelcomeMessage()">Click Me</button>
  </form>

</body>
</html>
''')
    
def lang():
    print('''
<!DOCTYPE html>
<html>
<head>
  <title>Programming Languages List</title>
</head>
<body>

  <h3>Programming Languages</h3>

  <ol type="I">
    <li>C</li>
    <li>C++</li>
    <li>Fortran</li>
    <li>COBOL</li>
  </ol>

</body>
</html>
''')
    
def array():
    print('''
<!DOCTYPE html>
<html>
<head>
  <title>Find Largest in Array</title>
  <script>
    function findLargest() {
      let input = document.getElementById("arrayInput").value;
      let arr = input.split(",").map(Number);
      let largest = Math.max(...arr);
      document.getElementById("result24").innerText = "Largest value: " + largest;
    }
  </script>
</head>
<body>
  <h3>24. Largest Value in Array</h3>
  <input type="text" id="arrayInput" placeholder="Enter numbers separated by commas">
  <button onclick="findLargest()">Find Largest</button>
  <p id="result24"></p>
</body>
</html>
          ''')
    
def summul():
    print('''
<!DOCTYPE html>
<html>
<head>
  <title>Sum and Multiplication</title>
  <script>
    function calculate() {
      let num1 = parseFloat(document.getElementById("num1").value);
      let num2 = parseFloat(document.getElementById("num2").value);
      let sum = num1 + num2;
      let product = num1 * num2;
      document.getElementById("result25").innerHTML = `Sum: ${sum}<br>Multiplication: ${product}`;
    }
  </script>
</head>
<body>
  <h3>25. Sum and Multiplication</h3>
  <input type="number" id="num1" placeholder="Enter first number">
  <input type="number" id="num2" placeholder="Enter second number">
  <button onclick="calculate()">Calculate</button>
  <p id="result25"></p>
</body>
</html>
          ''')
    
def cricket():
    print('''
<!DOCTYPE html>
<html>
<head>
  <title>Cricket Players List</title>
  <style>
    .one ::marker {
      font-weight: bold;
    }
  </style>
  
</head>
<body>
  <h3>23. Write the HTML coding to display the following:</h3>
  <ol>
    <li>Cricket players
      <ol class="one">
        <li><b>Batsman</b>
          <ol class="one" >
            <li>Sachin Tendulkara</li>
            <li>Rahul Dravid</li>
            <li><u>Virendrasehwag</u></li>
          </ol>
        </li>
        <li><b>Bowler</b>
          <ol class="one">
            <li>Kumbale</li>
            <li>Zaheer Khan</li>
            <li>Balaji</li>
          </ol>
        </li>
        <li><b>Spinner</b>
          <ol class="one">
            <li>Harbhajan</li>
            <li>Kumbale</li>
            <li>Jadeja</li>
          </ol>
        </li>
      </ol>
    </li>
  </ol>
</body>
</html>
          ''')

def frame():
    print('''
frame.html
<!DOCTYPE html>
<html>
<head>
    <title>Frames Example</title>
</head>

<frameset rows="90%,10%">
    <frameset cols="20%,80%">
        <frame src="left.html" name="leftFrame">
        <frame src="right.html" name="rightFrame">
    </frameset>
    <frame src="bottom.html" name="bottomFrame">
</frameset>

</html>

bottom.html
<!DOCTYPE html>
<html>
<head>
    <title>Bottom Frame</title>
</head>
<body style="background-color: #dddddd; text-align: center;">
    <p>Footer Information - 2025</p>
</body>
</html>
''')
