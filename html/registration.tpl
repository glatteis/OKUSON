<?xml version="1.0" encoding="ISO-8859-1"?>

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1" />
    <meta http-equiv="Expires" content="now" />
    <meta http-equiv="Cache-Control" content="no-cache" />
    <meta http-equiv="Pragma" content="no-cache" />

    <link href="/OKUSON.css" type="text/css" rel="StyleSheet" />

    <title>Anmeldung zu den �bungen</title>
  </head>

  <body>
    <h1>Anmeldung zu den �bungen</h1>

    <h2>Vorlesung: <CourseName />, <Semester />, <Lecturer /></h2>

<p>Die folgenden Daten werden nur zur Verwaltung des �bungsbetriebes und
zu statistischen Zwecken benutzt. F�r den Abruf von �bungsbl�ttern und
Ergebnissen brauchen Sie jeweils nur Ihre Matrikelnummer (ID) und Ihr Passwort.
</p>

<form action="/SubmitRegistration" method="post">
  <table>
    <tr>
      <td> <strong>Notwendige Angaben:</strong> </td>
      <td></td>
    </tr>

    <tr>
      <td>Matrikelnummer:</td>
      <td> <input size="8" maxlength="6" name="id" value="" /> </td>
    </tr>

    <tr>
      <td>Nachname:</td>
      <td> <input size="30" maxlength="30" name="lname" value="" /> </td>
    </tr>

    <tr>
      <td>Vorname:</td>
      <td> <input size="30" maxlength="30" name="fname" value="" /> </td>
    </tr>

    <tr>
      <td>Studiengang:</td>
      <td> <select name="stud">
             <PossibleStudies />
           </select>
        <input size="18" maxlength="30" name="topic" value="" />
        (falls "Sonstiges:").
      </td>
    </tr>

    <tr>
      <td>Fachsemester:</td>
      <td> <input size="2" maxlength="2" name="sem" value="" /> </td>
    </tr>

    <tr>
      <td>Passwort (<a href="hinwpasswd.html">HINWEIS</a>):</td>
      <td> <input type="password" size="16" maxlength="16" name="passwd"
        value="" />
      </td>
    </tr>

    <tr>
      <td>Passwort nochmal:</td>
      <td>
        <input type="password" size="16" maxlength="16" name="passwd2"
        value="" />
      </td>
    </tr>

    <!-- The following should be activated if you allow participants to
         choose their tutoring group number (see <GroupChoicePossible> in
         Config.xml . -->
    <!--
    <tr>
      <td>�bungsgruppennummer:</td>
      <td> <input size="3" maxlength="3" name="groupnr" value="" /> </td>
    </tr>
    -->

    <tr>
      <td> <strong>Freiwillige Angaben:</strong> </td>
      <td></td>
    </tr>

    <tr>
      <td>Email:</td>
      <td> <input size="30" maxlength="80" name="email" value="" /> </td>
    </tr>

    <tr>
      <td>Einteilungswunsch:</td>
      <td> <input size="30" maxlength="80" name="wishes" value="" /> </td>
    </tr>

    <tr>
      <td> </td>
      <td> <input type="submit" name="Action" value="Abschicken" /> </td>
    </tr>
  </table>

  <p>Bitte geben Sie unter "Einteilungswunsch" die Matrikelnummern
  der Kommilitoninnen/Kommilitonen ein, mit denen Sie zusammen in eine
  �bungsgruppe eingeteilt werden m�chten. Trennen Sie die Nummern
  durch L�cken oder Kommas.</p>
</form>

    <hr />

    <p><a href="/index.html">Zur�ck zur Startseite</a></p>

    <p class="foot">Bei Fragen wenden Sie sich bitte an: <br />
      <Feedback /> 
    </p>

    <p class="foot">
      <ValidatorIcon />
    </p>
  </body>
</html>

<!-- Copyright 2003 Frank L�beck and Max Neunh�ffer
     $Id: registration.tpl,v 1.2 2004/03/05 13:25:03 neunhoef Exp $ -->

