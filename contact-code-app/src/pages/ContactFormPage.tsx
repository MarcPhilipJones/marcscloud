/**
 * ContactFormPage — Create / Edit contact form.
 *
 * Placeholder — full implementation pending Dataverse SDK integration.
 */

import {
  makeStyles,
  tokens,
  shorthands,
  Title3,
  Body1,
  Button,
} from "@fluentui/react-components";
import { ArrowLeftRegular } from "@fluentui/react-icons";
import { useNavigate, useParams } from "react-router-dom";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    ...shorthands.gap("16px"),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.padding("40px"),
  },
});

export function ContactFormPage() {
  const styles = useStyles();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  return (
    <div className={styles.root}>
      <Title3>{id ? "Edit Contact" : "New Contact"}</Title3>
      <Body1>
        Contact form will be available after Dataverse SDK integration via{" "}
        <code>pac code add-data-source</code>.
      </Body1>
      <Button
        icon={<ArrowLeftRegular />}
        appearance="secondary"
        onClick={() => navigate(-1)}
      >
        Go Back
      </Button>
    </div>
  );
}
